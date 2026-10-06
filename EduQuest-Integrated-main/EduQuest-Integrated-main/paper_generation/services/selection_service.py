"""Constraint-based question selection and paper output construction.

Updated to work with 94-mark RUA allocation and question-count difficulty ratios.
"""

import json
import random
from ortools.sat.python import cp_model
from pathlib import Path


class SelectionService:
    """
    Select generated questions satisfying RUA on full paper,
    then add internal choices while preserving generated-paper difficulty ratios.
    
    RUA scope: Generated paper (94 marks)
    Difficulty scope: Generated paper (27 questions)
    """

    def check_feasibility(self, candidates, blueprint):
        """Return a structured feasibility report for the given blueprint."""

        rua_allocation = blueprint["requirements"]["rua_allocation"]
        pattern = blueprint["question_pattern"]
        unique_candidates = self._unique_candidates(candidates)

        issues = []

        # ---------------------------------------------------------
        # 1. Check every Unit + RUA marks requirement
        # ---------------------------------------------------------
        for unit, allocation in rua_allocation.items():
            for rua in ("R", "U", "A"):
                target = allocation.get(rua, 0)

                if target == 0:
                    continue

                pool = [
                    q for q in unique_candidates
                    if q["unit"] == unit and q["rua"] == rua
                ]

                available_total_marks = sum(q["marks"] for q in pool)
                available_question_marks = sorted(
                    set(q["marks"] for q in pool)
                )

                if available_total_marks < target:
                    issues.append({
                        "type": "RUA_MARKS",
                        "unit": unit,
                        "rua": rua,
                        "requested_marks": target,
                        "available_total_marks": available_total_marks,
                        "available_question_marks": available_question_marks,
                        "available_question_count": len(pool),
                        "reason": (
                            "Insufficient total marks available for this "
                            "Unit/RUA requirement."
                        )
                    })
                    continue

                if not self._find_mark_combination(pool, target):
                    issues.append({
                        "type": "RUA_MARKS",
                        "unit": unit,
                        "rua": rua,
                        "requested_marks": target,
                        "available_total_marks": available_total_marks,
                        "available_question_marks": available_question_marks,
                        "available_question_count": len(pool),
                        "reason": (
                            "Requested marks cannot be formed from the "
                            "available questions."
                        )
                    })

        # ---------------------------------------------------------
        # 2. Check question-pattern availability
        # ---------------------------------------------------------
        required_by_marks = {}

        for section in pattern.values():
            marks = section["marks_per_question"]
            required_by_marks[marks] = (
                required_by_marks.get(marks, 0)
                + section["questions_to_generate"]
            )

        for marks, required_count in required_by_marks.items():
            available_count = len([
                q for q in unique_candidates
                if q["marks"] == marks
            ])

            if available_count < required_count:
                issues.append({
                    "type": "QUESTION_PATTERN",
                    "marks_per_question": marks,
                    "required_question_count": required_count,
                    "available_question_count": available_count,
                    "reason": (
                        f"Insufficient {marks}-mark questions "
                        "for the requested question pattern."
                    )
                })
                # ---------------------------------------------------------
        # 3. Check GLOBAL RUA vs question-pattern compatibility
        # ---------------------------------------------------------
        #
        # Individual Unit/RUA groups may each be feasible but still
        # be impossible to satisfy together under the global 2M/4M
        # question pattern.
        #
        # Example:
        #   6 marks  = 4 + 2
        #   10 marks = 4 + 4 + 2
        #
        # Therefore targets such as 2, 6 and 10 require at least
        # one 2-mark question when only 2M and 4M questions exist.
        # ---------------------------------------------------------

        allowed_2m_questions = required_by_marks.get(2, 0)
        allowed_4m_questions = required_by_marks.get(4, 0)

        minimum_2m_questions = 0
        minimum_4m_questions = 0

        group_requirements = []

        for unit, allocation in rua_allocation.items():

            for rua in ("R", "U", "A"):

                target = allocation.get(rua, 0)

                if target <= 0:
                    continue

                # ---------------------------------------------
                # Find minimum number of 2M questions required
                # to form this exact target using 2M and 4M.
                # ---------------------------------------------

                group_min_2m = None
                group_min_4m = None

                for two_count in range(
                    (target // 2) + 1
                ):

                    remaining = target - (two_count * 2)

                    if remaining < 0:
                        continue

                    if remaining % 4 != 0:
                        continue

                    four_count = remaining // 4

                    group_min_2m = two_count
                    group_min_4m = four_count
                    break

                # Target itself cannot be represented by 2M/4M
                if group_min_2m is None:
                    continue

                minimum_2m_questions += group_min_2m
                minimum_4m_questions += group_min_4m

                group_requirements.append({
                    "unit": unit,
                    "rua": rua,
                    "target_marks": target,
                    "minimum_2m": group_min_2m,
                    "minimum_4m": group_min_4m
                })

        if minimum_2m_questions > allowed_2m_questions:

            issues.append({
                "type": "GLOBAL_RUA_PATTERN",
                "required_minimum_2_mark_questions":
                    minimum_2m_questions,
                "allowed_2_mark_questions":
                    allowed_2m_questions,
                "required_minimum_4_mark_questions":
                    minimum_4m_questions,
                "allowed_4_mark_questions":
                    allowed_4m_questions,
                "group_requirements":
                    group_requirements,
                "reason": (
                    "RUA allocation is incompatible with the "
                    "global question pattern. The Unit/RUA "
                    "targets collectively require more 2-mark "
                    "questions than the question pattern allows."
                )
            })

        # ---------------------------------------------------------
        # 4. Check difficulty availability
        # ---------------------------------------------------------
        available_options = {
            "marks": sorted(set(
                q["marks"] for q in unique_candidates
            )),
            "rua": sorted(set(
                q["rua"] for q in unique_candidates
            )),
            "difficulty": sorted(set(
                q["difficulty"] for q in unique_candidates
            ))
        }

        paper_info = blueprint.get("paper_information", {})

        blueprint_id = (
            blueprint.get("blueprint_id")
            or paper_info.get("blueprint_id")
            or paper_info.get("subject_code")
        )

        return {
            "status": "FEASIBLE" if not issues else "INFEASIBLE",
            "blueprint_id": blueprint_id,
            "issues": issues,
            "available_options": available_options
        }

    def generate_selection(
        self,
        candidates,
        blueprint,
        usage_counts=None,
        seed=None,
    ):
        """Generate an exact blueprint-compliant paper using CP-SAT."""
        feasibility = self.check_feasibility(candidates, blueprint)
        if feasibility["status"] != "FEASIBLE":
            raise ValueError("BLUEPRINT_INFEASIBLE: " + json.dumps(feasibility["issues"], ensure_ascii=False))
        generated_questions = self.select_generated_questions(
            candidates,
            blueprint,
            usage_counts=usage_counts,
            seed=seed,
        )
        sections = self._build_sections(generated_questions, blueprint)
        output = {"paper_information": blueprint["paper_information"], "sections": sections}
        self.validate_selection(output, blueprint)
        output["reference_attempted_selection"] = self._reference_attempted_selection(sections, blueprint)
        generated = [q for section in sections.values() for q in section["questions"]]
        difficulty_result = self.validate_generated_difficulty(generated, blueprint)
        output["difficulty_status"] = difficulty_result["status"]
        output["difficulty_distribution"] = difficulty_result
        if difficulty_result["status"] != "VALID":
            raise ValueError(f"DIFFICULTY_PATTERN_INVALID: expected {difficulty_result['target_marks']}, got {difficulty_result['difficulty_marks']}")
        return output

    def select_generated_questions(
        self,
        candidates,
        blueprint,
        usage_counts=None,
        seed=None,
    ):
        """Select exact generated-paper questions with CP-SAT."""
        unique_candidates = self._unique_candidates(candidates)
        has_usage_counts = usage_counts is not None
        usage_counts = usage_counts or {}
        rng = random.Random(seed)
        unique_candidates.sort(
            key=lambda q: (
                usage_counts.get(q["canonical_id"], 0),
                rng.random(),
            )
        )
        if not unique_candidates:
            raise ValueError("UNSATISFIABLE_SELECTION: no candidates available")
        pattern = blueprint["question_pattern"]
        requirements = blueprint["requirements"]
        required_counts = {}
        for section in pattern.values():
            marks = int(section["marks_per_question"])
            required_counts[marks] = required_counts.get(marks, 0) + int(section["questions_to_generate"])
        total_questions = sum(required_counts.values())
        total_marks = sum(m*c for m,c in required_counts.items())
        difficulty_targets = {k:int(v) for k,v in requirements.get("difficulty_allocation", {}).items()}
        if difficulty_targets and sum(difficulty_targets.values()) != total_marks:
            raise ValueError(f"DIFFICULTY_TOTAL_INVALID: expected {total_marks}, got {sum(difficulty_targets.values())}")
        rua_targets = {(u,r):int(a.get(r,0)) for u,a in requirements["rua_allocation"].items() for r in ("R","U","A")}
        if sum(rua_targets.values()) != total_marks:
            raise ValueError(f"RUA_TOTAL_INVALID: expected {total_marks}, got {sum(rua_targets.values())}")
        model = cp_model.CpModel()
        x = [model.NewBoolVar(f"q_{i}") for i in range(len(unique_candidates))]
        model.Add(sum(x) == total_questions)
        allowed_marks=set(required_counts)
        for marks,target in required_counts.items():
            ids=[i for i,q in enumerate(unique_candidates) if int(q["marks"])==marks]
            if len(ids)<target: raise ValueError(f"QUESTION_PATTERN_UNSATISFIABLE: need {target} {marks}-mark questions, have {len(ids)}")
            model.Add(sum(x[i] for i in ids)==target)
        for i,q in enumerate(unique_candidates):
            if int(q["marks"]) not in allowed_marks: model.Add(x[i]==0)
        valid_slots=set(rua_targets)
        for slot,target in rua_targets.items():
            ids=[i for i,q in enumerate(unique_candidates) if (q["unit"],q["rua"])==slot]
            model.Add(sum(int(unique_candidates[i]["marks"])*x[i] for i in ids)==target)
        for i,q in enumerate(unique_candidates):
            if (q["unit"],q["rua"]) not in valid_slots: model.Add(x[i]==0)
        for difficulty,target in difficulty_targets.items():
            ids=[i for i,q in enumerate(unique_candidates) if q["difficulty"]==difficulty]
            model.Add(sum(int(unique_candidates[i]["marks"])*x[i] for i in ids)==target)
        if difficulty_targets:
            valid_diff=set(difficulty_targets)
            for i,q in enumerate(unique_candidates):
                if q["difficulty"] not in valid_diff: model.Add(x[i]==0)
        for co in set(requirements.get("co_requirements", [])):
            ids=[i for i,q in enumerate(unique_candidates) if q.get("course_outcome")==co]
            if not ids: raise ValueError(f"MISSING_GENERATED_CO_COVERAGE: no candidate for {co}")
            model.Add(sum(x[i] for i in ids)>=1)
        n=len(unique_candidates)
        if has_usage_counts:
            usage_weight = total_questions * max(n - 1, 0) + 1
            model.Minimize(sum(
                (
                    int(usage_counts.get(q["canonical_id"], 0)) * usage_weight
                    + i
                ) * x[i]
                for i, q in enumerate(unique_candidates)
            ))
        else:
            model.Minimize(sum((int(q.get("_usage_count",0) or 0)*(n+1)+i)*x[i] for i,q in enumerate(unique_candidates)))
        solver=cp_model.CpSolver(); solver.parameters.max_time_in_seconds=15.0; solver.parameters.num_search_workers=8; solver.parameters.random_seed=0
        if seed is not None:
            solver.parameters.num_search_workers = 1
        status=solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise ValueError(f"UNSATISFIABLE_SELECTION: solver status {solver.StatusName(status)}")
        selected=[q for i,q in enumerate(unique_candidates) if solver.Value(x[i])]
        selected.sort(key=lambda q:(int(q["marks"]),str(q["unit"]),str(q["rua"]),str(q["difficulty"]),str(q["canonical_id"])))
        return selected

    def generate_selected_questions_json(self, candidates, blueprint, output_path=None):
        """Generate and export the validated selection."""
        output = self.generate_selection(candidates, blueprint)
        self.export_selected_questions(output, blueprint, output_path)
        return output

    def export_selected_questions(self, selection, blueprint, output_path=None):
        """Export a validated selection using Anushka's formatter contract."""
        self.validate_selection(selection, blueprint)
        generated = [
            question
            for section in selection["sections"].values()
            for question in section["questions"]
        ]
        difficulty = self.validate_generated_difficulty(generated, blueprint)
        if difficulty["status"] != "VALID":
            raise ValueError(
                f"DIFFICULTY_PATTERN_INVALID: expected {difficulty['target_marks']}, "
                f"got {difficulty['difficulty_marks']}"
            )

        destination = Path(output_path or "selected_questions.json")
        if destination.name == "selected_questions_sample.json":
            raise ValueError("EXPORT_BLOCKED: sample output must not be overwritten")

        question_fields = (
            "canonical_id",
            "question_text",
            "unit",
            "marks",
            "rua",
            "difficulty",
            "course_outcome",
        )
        paper_information = {
            key: value
            for key, value in blueprint["paper_information"].items()
            if key != "attempted_total_marks"
        }
        paper_information["paper_total_marks"] = blueprint["paper_information"].get(
            "attempted_total_marks", paper_information["paper_total_marks"]
        )
        exported = {
            "paper_information": paper_information,
            "sections": {},
        }
        for name, section in selection["sections"].items():
            exported["sections"][name] = {
                "questions_to_attempt": section["questions_to_attempt"],
                "questions": [
                    {field: question[field] for field in question_fields}
                    for question in section["questions"]
                ],
            }

        destination.write_text(json.dumps(exported, indent=2), encoding="utf-8")
        return exported

    def validate_selection(self, output, blueprint):
        """
        Validate the complete selection:
        - Generated paper: 27 questions, 94 marks, RUA exact match
        - Attempted paper: 70 marks, difficulty exact match, CO coverage
        """
        sections = output["sections"]
        pattern = blueprint["question_pattern"]
        
        # === GENERATED PAPER VALIDATION ===
        all_questions = [
            q for section in sections.values()
            for q in section["questions"]
        ]
        
        # Check uniqueness
        ids = [q["canonical_id"] for q in all_questions]
        if len(ids) != len(set(ids)):
            raise ValueError("DUPLICATE_CANONICAL_ID: selected questions are not unique")
        
        # Check count
        expected_count = sum(s["questions_to_generate"] for s in pattern.values())
        if len(all_questions) != expected_count:
            raise ValueError(
                f"QUESTION_PATTERN_UNSATISFIABLE: expected {expected_count} "
                f"questions, got {len(all_questions)}"
            )
        
        # Check marks per section
        for name, section in sections.items():
            expected = pattern[name]
            if len(section["questions"]) != expected["questions_to_generate"]:
                raise ValueError(
                    f"QUESTION_PATTERN_UNSATISFIABLE: {name} count invalid"
                )
            if any(q["marks"] != expected["marks_per_question"] for q in section["questions"]):
                raise ValueError(
                    f"QUESTION_PATTERN_UNSATISFIABLE: {name} marks invalid"
                )
        
        # Check total generated marks
        total_generated = sum(q["marks"] for q in all_questions)
        if total_generated != 94:
            raise ValueError(
                f"GENERATED_MARKS_INVALID: expected 94, got {total_generated}"
            )

        mark_counts = {marks: sum(q["marks"] == marks for q in all_questions) for marks in (2, 4)}
        expected_mark_counts = {
            marks: sum(
                section["questions_to_generate"]
                for section in pattern.values()
                if section["marks_per_question"] == marks
            )
            for marks in (2, 4)
        }
        if mark_counts != expected_mark_counts:
            raise ValueError(
                f"UNSATISFIABLE_PATTERN: expected mark counts "
                f"{expected_mark_counts}, got {mark_counts}"
            )
        
        # Validate RUA against GENERATED paper (all 94 marks)
        actual_rua = {}
        for q in all_questions:
            key = (q["unit"], q["rua"])
            actual_rua[key] = actual_rua.get(key, 0) + q["marks"]
        
        required_rua = blueprint["requirements"]["rua_allocation"]
        for unit, allocation in required_rua.items():
            for rua in ("R", "U", "A"):
                required = allocation.get(rua, 0)
                actual = actual_rua.get((unit, rua), 0)
                if actual != required:
                    raise ValueError(
                        f"UNSATISFIABLE_RUA: {unit} {rua}\n"
                        f"  Required: {required} marks\n"
                        f"  Actual: {actual} marks"
                    )
        
        # CO coverage is a generated-paper requirement.
        required_cos = set(blueprint["requirements"].get("co_requirements", []))
        actual_cos = {q["course_outcome"] for q in all_questions}
        missing_cos = required_cos - actual_cos
        if missing_cos:
            raise ValueError(f"MISSING_GENERATED_CO_COVERAGE: {sorted(missing_cos)}")

        attempted = self._reference_attempted_selection(sections, blueprint)
        expected_attempted_count = sum(
            section["questions_to_attempt"] for section in sections.values()
        )
        expected_attempted_marks = blueprint["paper_information"].get(
            "attempted_total_marks", 70
        )
        if len(attempted) != expected_attempted_count:
            raise ValueError(
                f"ATTEMPTED_PATTERN_INVALID: expected {expected_attempted_count} "
                f"questions, got {len(attempted)}"
            )
        attempted_marks = sum(q["marks"] for q in attempted)
        if attempted_marks != expected_attempted_marks:
            raise ValueError(
                f"ATTEMPTED_MARKS_INVALID: expected {expected_attempted_marks}, "
                f"got {attempted_marks}"
            )

    def validate_generated_difficulty(self, generated, blueprint):
        """Validate exact difficulty marks across the full generated paper."""

        targets = dict(
            blueprint["requirements"]["difficulty_allocation"]
        )

        actual = {
            difficulty: sum(
                q["marks"]
                for q in generated
                if q["difficulty"] == difficulty
            )
            for difficulty in targets
        }

        return {
            "status": "VALID" if actual == targets else "INVALID",
            "difficulty_marks": actual,
            "target_marks": targets,
        }

    def diagnose_difficulty_gap(self, candidates, generated, blueprint):
        """Explain difficulty mark gaps and possible same-slot replacements."""

        targets = dict(
            blueprint["requirements"]["difficulty_allocation"]
        )

        actual = {
            difficulty: sum(
                q["marks"]
                for q in generated
                if q["difficulty"] == difficulty
            )
            for difficulty in targets
        }
        by_slot = {}
        for question in candidates:
            slot = (question["unit"], question["rua"], question["marks"])
            by_slot.setdefault(slot, []).append(question)

        forced_hard = []
        replaceable_hard = []
        for question in generated:
            if question["difficulty"] != "Hard":
                continue
            alternatives = [
                candidate for candidate in by_slot[
                    (question["unit"], question["rua"], question["marks"])
                ] if candidate["difficulty"] != "Hard"
            ]
            (replaceable_hard if alternatives else forced_hard).append(
                question["canonical_id"]
            )

        mock_requirements = []
        for difficulty, deficit in (
            ("Easy", targets["Easy"] - actual["Easy"]),
            ("Medium", targets["Medium"] - actual["Medium"]),
        ):
            if deficit <= 0:
                continue
            donor_slots = {}
            for question in generated:
                if question["difficulty"] == difficulty:
                    continue
                slot = (question["unit"], question["rua"], question["marks"])
                if any(
                    candidate["difficulty"] == difficulty
                    for candidate in by_slot[slot]
                ):
                    continue
                donor_slots[slot] = donor_slots.get(slot, 0) + 1
            if donor_slots:
                slot, available = max(
                    donor_slots.items(), key=lambda item: (item[1], item[0])
                )
                mock_requirements.append({
                    "difficulty": difficulty,
                    "count": min(deficit, available),
                    "unit": slot[0],
                    "rua": slot[1],
                    "marks": slot[2],
                })

        return {
           "target_marks": targets,
            "actual_marks": actual,
            "forced_hard_selections": forced_hard,
            "replaceable_hard_selections": replaceable_hard,
            "mock_requirements": mock_requirements,
        }


    @staticmethod
    def _reference_attempted_selection(sections, blueprint):
        """Return a representative option set without claiming it is unique."""
        attempted = []
        for name, section in sections.items():
            attempted.extend(
                section["questions"][:blueprint["question_pattern"][name]["questions_to_attempt"]]
            )
        return attempted

    def select_by_unit_and_rua(self, candidates, blueprint):
        """Select questions for exact Unit/RUA allocation."""
        selected_questions = []
        used_canonical_ids = set()
        
        for unit, allocation in blueprint["requirements"]["rua_allocation"].items():
            for rua_level in ("R", "U", "A"):
                target = allocation.get(rua_level, 0)
                if target == 0:
                    continue
                
                pool = [
                    q for q in candidates
                    if q["unit"] == unit
                    and q["rua"] == rua_level
                    and q["canonical_id"] not in used_canonical_ids
                ]
                
                combination = self._find_mark_combination(pool, target)
                if combination is None:
                    available = sum(q["marks"] for q in pool)
                    raise ValueError(
                        f"UNSATISFIABLE_RUA: {unit} {rua_level}\n"
                        f"  Required: {target} marks\n"
                        f"  Available: {available} marks"
                    )
                
                selected_questions.extend(combination)
                used_canonical_ids.update(
                    q["canonical_id"] for q in combination
                )
        
        return selected_questions

    def select_attempted_questions(self, candidates, blueprint):
        """Find unique attempted question set satisfying attempted blueprint."""
        pattern = blueprint["question_pattern"]
        
        # Build slots for attempted questions
        slots = [
            section["marks_per_question"]
            for section in pattern.values()
            for _ in range(section["questions_to_attempt"])
        ]
        
        # RUA targets are from the generated paper (94 marks)
        rua_targets = {
            (unit, rua): allocation.get(rua, 0)
            for unit, allocation in blueprint["requirements"]["rua_allocation"].items()
            for rua in ("R", "U", "A")
        }
        
        # Difficulty targets are from attempted paper (70 marks)
        difficulty_targets = blueprint["requirements"].get("difficulty_allocation", {})
        required_cos = set(blueprint["requirements"].get("co_requirements", []))
        
        unique_candidates = self._unique_candidates(candidates)
        by_marks = {
            marks: [q for q in unique_candidates if q["marks"] == marks]
            for marks in set(slots)
        }
        
        # Validate we have enough questions of each mark
        for marks, count in ((2, slots.count(2)), (4, slots.count(4))):
            if count and len(by_marks.get(marks, [])) < count:
                raise ValueError(
                    f"QUESTION_PATTERN_UNSATISFIABLE: need {count} unique "
                    f"{marks}-mark questions, have {len(by_marks.get(marks, []))}"
                )
        
        # Search for valid combination
        ordered_slots = sorted(slots, key=lambda m: len(by_marks[m]))
        result = self._search_attempted(
            ordered_slots, by_marks, rua_targets, difficulty_targets,
            required_cos, [], set(), {}, {}, set()
        )
        
        if result is None:
            raise ValueError(
                "UNSATISFIABLE_DIFFICULTY or UNSATISFIABLE_RUA: "
                "no valid attempted question set exists"
            )
        
        return result

    @staticmethod
    def _find_mark_combination(pool, target):
        """Find one exact mark subset with bounded dynamic programming."""
        if target == 0: return ()
        reachable={0:()}
        for q in pool:
            marks=int(q["marks"])
            for subtotal,chosen in list(reachable.items()):
                new=subtotal+marks
                if new>target or new in reachable: continue
                reachable[new]=chosen+(q,)
                if new==target: return reachable[new]
        return reachable.get(target)

    @staticmethod
    def _unique_candidates(candidates):
        """Return unique candidates by canonical_id."""
        unique = {}
        for q in candidates:
            unique.setdefault(q["canonical_id"], q)
        return list(unique.values())

    def _search_attempted(self, slots, by_marks, rua_targets, difficulty_targets,
                          required_cos, selected, used_ids, rua_totals,
                          difficulty_totals, covered_cos):
        """Backtracking search for valid attempted question set."""
        if not slots:
            # Check if all targets met
            if rua_totals != {k: v for k, v in rua_targets.items() if v}:
                return None
            if difficulty_totals != {k: v for k, v in difficulty_targets.items() if v}:
                return None
            if not required_cos.issubset(covered_cos):
                return None
            return selected
        
        marks = slots[0]
        for q in by_marks[marks]:
            if q["canonical_id"] in used_ids:
                continue
            
            # Check RUA constraint
            rua_key = (q["unit"], q["rua"])
            new_rua = dict(rua_totals)
            new_rua[rua_key] = new_rua.get(rua_key, 0) + marks
            if new_rua[rua_key] > rua_targets.get(rua_key, 0):
                continue
            
            # Check difficulty constraint
            new_difficulty = dict(difficulty_totals)
            diff = q["difficulty"]
            new_difficulty[diff] = new_difficulty.get(diff, 0) + marks
            if new_difficulty[diff] > difficulty_targets.get(diff, 0):
                continue
            
            # Recurse
            found = self._search_attempted(
                slots[1:], by_marks, rua_targets, difficulty_targets,
                required_cos, selected + [q], used_ids | {q["canonical_id"]},
                new_rua, new_difficulty, covered_cos | {q["course_outcome"]}
            )
            
            if found is not None:
                return found
        
        return None

    @staticmethod
    def _build_sections(generated_questions, blueprint):
        """Assign generated questions to sections by their required mark value."""
        pools = {}
        for question in generated_questions:
            pools.setdefault(question["marks"], []).append(question)

        sections = {}
        for name, pattern in blueprint["question_pattern"].items():
            count = pattern["questions_to_generate"]
            marks = pattern["marks_per_question"]
            pool = pools.setdefault(marks, [])
            if len(pool) < count:
                raise ValueError(
                    f"QUESTION_PATTERN_UNSATISFIABLE: {name}\n"
                    f"  Required: {count} questions of {marks} marks\n"
                    f"  Available: {len(pool)}"
                )

            section_questions = pool[:count]
            del pool[:count]
            if any(question["marks"] != marks for question in section_questions):
                raise ValueError(
                    f"QUESTION_PATTERN_UNSATISFIABLE: {name} marks invalid"
                )
            sections[name] = {
                "questions_to_attempt": pattern["questions_to_attempt"],
                "questions": section_questions,
            }

        assigned = [
            question
            for section in sections.values()
            for question in section["questions"]
        ]
        assigned_ids = [question["canonical_id"] for question in assigned]
        generated_ids = [question["canonical_id"] for question in generated_questions]
        if len(assigned) != len(generated_questions) or set(assigned_ids) != set(generated_ids):
            raise ValueError(
                "QUESTION_PATTERN_UNSATISFIABLE: generated questions were not "
                "assigned exactly once"
            )
        if len(assigned_ids) != len(set(assigned_ids)):
            raise ValueError(
                "QUESTION_PATTERN_UNSATISFIABLE: duplicate assigned question"
            )
        
        return sections

    @staticmethod
    def _compatibility_score(question, base_question):
        """Score how compatible a question is with a base question."""
        weights = {
            "unit": 8,
            "rua": 6,
            "difficulty": 3,
            "course_outcome": 1,
        }
        return sum(
            (question[field] == base_question[field]) * weight
            for field, weight in weights.items()
        )
