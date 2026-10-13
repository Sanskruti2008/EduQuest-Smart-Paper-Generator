import os
import sys
import tempfile
import shutil
import time
from pathlib import Path

from dotenv import load_dotenv
from flask import Blueprint, current_app, g, jsonify, request, send_file
from postgrest.exceptions import APIError
from utils.auth import require_supabase_roles
from services.generation_executor import (
    GenerationBusyError,
    GenerationTimeoutError,
    generation_executor,
)

generation_bp = Blueprint("generation_bp", __name__)


@generation_bp.route("/api/generated-papers/<int:paper_id>", methods=["GET"])
@require_supabase_roles("admin", "faculty")
def get_generated_paper(paper_id):
    try:
        from database import get_supabase_admin_client

        client = get_supabase_admin_client()
        log_query = (
            client.table("papergenerationlog")
            .select("paper_id,generation_id,generated_at,generated_by,total_questions,total_marks")
            .eq("paper_id", paper_id)
            .limit(1)
        )
        if str(g.current_user.get("role", "")).lower() == "faculty":
            log_query = log_query.eq("generated_by", g.current_user["user_id"])
        log_rows = log_query.execute().data or []
        if not log_rows:
            return jsonify({"success": False, "error": "Generated paper not found."}), 404

        paper_rows = (
            client.table("questionpaper")
            .select("paper_id,raw_json")
            .eq("paper_id", paper_id)
            .limit(1)
            .execute()
        ).data or []
        if not paper_rows:
            return jsonify({"success": False, "error": "Generated paper not found."}), 404

        raw_json = paper_rows[0].get("raw_json") or {}
        blueprint = raw_json.get("blueprint") or {}
        selection = raw_json.get("selection") or {}
        return jsonify({
            "success": True,
            "paper": {
                **log_rows[0],
                "paper_information": selection.get("paper_information")
                    or blueprint.get("paper_information")
                    or {},
                "sections": selection.get("sections") or {},
            },
        }), 200
    except Exception:
        current_app.logger.exception("Unable to load generated paper")
        return jsonify({
            "success": False,
            "error": "Unable to load generated paper.",
        }), 500


@generation_bp.route("/api/generated-papers", methods=["GET"])
@require_supabase_roles("admin", "faculty")
def get_generated_papers():
    try:
        from database import get_supabase_admin_client

        client = get_supabase_admin_client()
        logs_query = (
            client.table("papergenerationlog")
            .select(
                "paper_id,generation_id,generated_at,generated_by,"
                "total_questions,total_marks"
            )
            .order("generated_at", desc=True)
        )
        if str(g.current_user.get("role", "")).lower() == "faculty":
            logs_query = logs_query.eq("generated_by", g.current_user["user_id"])

        logs = logs_query.execute().data or []
        paper_ids = [row["paper_id"] for row in logs if row.get("paper_id") is not None]
        if not paper_ids:
            return jsonify({"success": True, "papers": []}), 200

        papers = (
            client.table("questionpaper")
            .select("paper_id,subject_id,exam_type,exam_year,raw_json,created_at")
            .in_("paper_id", paper_ids)
            .execute()
        ).data or []
        subject_ids = list({
            row["subject_id"] for row in papers if row.get("subject_id") is not None
        })
        subjects = (
            client.table("subject")
            .select("subject_id,subject_name,subject_code,branch,semester")
            .in_("subject_id", subject_ids)
            .execute()
        ).data if subject_ids else []
        creator_ids = list({
            row["generated_by"] for row in logs if row.get("generated_by") is not None
        })
        creators = (
            client.table("User")
            .select("user_id,name,email")
            .in_("user_id", creator_ids)
            .execute()
        ).data if creator_ids else []
        subjects_by_id = {row["subject_id"]: row for row in (subjects or [])}
        creators_by_id = {row["user_id"]: row for row in (creators or [])}
        papers_by_id = {row["paper_id"]: row for row in papers}

        result = []
        for log in logs:
            paper = papers_by_id.get(log.get("paper_id"))
            if not paper:
                continue
            subject = subjects_by_id.get(paper.get("subject_id"), {})
            creator = creators_by_id.get(log.get("generated_by"), {})
            raw_json = paper.get("raw_json") or {}
            paper_information = raw_json.get("blueprint", {}).get("paper_information", {})
            result.append({
                "paper_id": paper["paper_id"],
                "generation_id": log.get("generation_id"),
                "title": (
                    f"{subject.get('subject_name') or paper_information.get('subject') or 'Question Paper'}"
                    f" - {paper.get('exam_type') or paper_information.get('exam_type') or 'Exam'}"
                ),
                "subject": subject.get("subject_name") or paper_information.get("subject") or "",
                "subject_code": subject.get("subject_code") or paper_information.get("subject_code") or "",
                "branch": subject.get("branch") or paper_information.get("branch") or "",
                "semester": subject.get("semester") or paper_information.get("semester") or "",
                "exam_type": paper.get("exam_type") or paper_information.get("exam_type") or "",
                "questions": log.get("total_questions") or 0,
                "marks": log.get("total_marks") or 0,
                "generated_at": log.get("generated_at") or paper.get("created_at"),
                "created_by": creator.get("name") or creator.get("email") or "Unknown faculty",
            })
        return jsonify({"success": True, "papers": result}), 200
    except Exception:
        current_app.logger.exception("Unable to load generated papers")
        return jsonify({
            "success": False,
            "error": "Unable to load generated papers.",
        }), 500
def _is_missing_generation_flag_error(error: APIError) -> bool:
    details = " ".join(
        str(value or "")
        for value in (
            getattr(error, "details", None),
            getattr(error, "message", None),
            error,
        )
    ).lower()
    return (
        "can_generate" in details
        and (
            "does not exist" in details
            or "unknown column" in details
            or "not found" in details
            or "could not find" in details
            or "schema cache" in details
        )
    )


def _get_faculty_generation_assignments(client, faculty_id: int, subject_id=None):
    query = (
        client.table("faculty_subject_assignment")
        .select("subject_id")
        .eq("faculty_id", faculty_id)
        .eq("is_active", True)
        .eq("can_generate", True)
    )
    if subject_id is not None:
        query = query.eq("subject_id", subject_id)

    try:
        return query.execute().data or []
    except APIError as exc:
        if not _is_missing_generation_flag_error(exc):
            raise

    legacy_query = (
        client.table("faculty_subject_assignment")
        .select("subject_id")
        .eq("faculty_id", faculty_id)
        .eq("is_active", True)
    )
    if subject_id is not None:
        legacy_query = legacy_query.eq("subject_id", subject_id)
    return legacy_query.execute().data or []


@generation_bp.route("/api/paper-generation/subjects", methods=["GET"])
@require_supabase_roles("admin", "faculty")
def get_paper_generation_subjects():
    try:
        from database import get_supabase_admin_client

        client = get_supabase_admin_client()
        subjects_query = (
            client.table("subject")
            .select("subject_id,subject_name,subject_code,branch,semester")
        )
        if str(g.current_user.get("role", "")).lower() == "faculty":
            assignments = _get_faculty_generation_assignments(
                client,
                g.current_user["user_id"],
            )
            subject_ids = [row["subject_id"] for row in assignments]
            if not subject_ids:
                return jsonify({"success": True, "subjects": []}), 200
            subjects_query = subjects_query.in_("subject_id", subject_ids)
        response = subjects_query.order("subject_name").execute()
        subjects = [
            {
                "subject_id": row["subject_id"],
                "subject_name": row["subject_name"],
                "subject_code": str(row.get("subject_code") or "").strip(),
                "branch": str(row.get("branch") or "").strip(),
                "semester": row.get("semester") or "",
            }
            for row in (response.data or [])
        ]
        return jsonify({
            "success": True,
            "subjects": subjects,
        }), 200
    except Exception:
        current_app.logger.exception("Unable to load subjects for paper generation")
        return jsonify({
            "success": False,
            "error": "Unable to load subjects for paper generation.",
        }), 500


_PIPELINE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "EduQuest-Integrated-main"
    / "EduQuest-Integrated-main"
)


@generation_bp.route("/api/generate-question-paper", methods=["POST"])
@require_supabase_roles("admin", "faculty")
def generate_question_paper():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"success": False, "error": "A JSON faculty input object is required."}), 400

    try:
        if str(g.current_user.get("role", "")).lower() == "faculty":
            subject_id = body.get("subject_id")
            if isinstance(subject_id, bool) or (
                isinstance(subject_id, float) and not subject_id.is_integer()
            ):
                subject_id = None
            try:
                subject_id = int(subject_id)
            except (TypeError, ValueError):
                subject_id = None
            if subject_id is None or subject_id <= 0:
                return jsonify({
                    "success": False,
                    "error": "Select an assigned subject before generating a paper.",
                }), 400
            from database import get_supabase_admin_client

            assignments = _get_faculty_generation_assignments(
                get_supabase_admin_client(),
                g.current_user["user_id"],
                subject_id=subject_id,
            )
            if not assignments:
                return jsonify({
                    "success": False,
                    "message": "You are not assigned as a paper setter for this subject.",
                }), 403

        selected_units = body.get("selected_units")
        rua_allocation = body.get("rua_allocation")
        if not isinstance(selected_units, list) or not isinstance(rua_allocation, dict):
            return jsonify({
                "success": False,
                "error": "selected_units and rua_allocation must be provided as matching collections.",
            }), 400
        missing_units = [
            str(unit) for unit in selected_units
            if str(unit) not in rua_allocation
        ]
        if missing_units:
            return jsonify({
                "success": False,
                "error": f"RUA allocation is missing selected units: {', '.join(missing_units)}",
            }), 400

        if not _PIPELINE_ROOT.is_dir():
            raise RuntimeError(f"Paper generation pipeline not found: {_PIPELINE_ROOT}")
        root = str(_PIPELINE_ROOT)
        if root not in sys.path:
            sys.path.insert(0, root)
        load_dotenv(
            Path(__file__).resolve().parents[1] / ".env",
            override=False,
        )

        output_dir = Path(tempfile.mkdtemp(prefix="eduquest-paper-"))
        from eduquest_pipeline import generate_final_question_paper

        generated_by = int(g.current_user["user_id"])
        started_at = time.perf_counter()
        generation_input = dict(body)
        generation_input["_generated_by"] = g.current_user.get("user_id")
        try:
            result = generation_executor.submit(
                lambda: generate_final_question_paper(
                    faculty_input=generation_input,
                    output_dir=str(output_dir),
                    persist=True,
                    generated_by=generated_by,
                )
            )
        except GenerationBusyError as error:
            shutil.rmtree(output_dir, ignore_errors=True)
            return jsonify({"success": False, "error": str(error)}), 429
        except GenerationTimeoutError as error:
            shutil.rmtree(output_dir, ignore_errors=True)
            return jsonify({"success": False, "error": str(error)}), 504

        if result.get("status") != "SUCCESS":
            shutil.rmtree(output_dir, ignore_errors=True)
            pipeline_error = result.get("error", "")
            if "BLUEPRINT_INFEASIBLE" in pipeline_error:
                message = (
                    "No eligible questions are available in the Unique Question Bank "
                    "for the selected subject, units, marks, and R/U/A requirements. "
                    "Upload and process questions first, or reduce the requested constraints."
                )
            else:
                message = pipeline_error or "The paper-generation pipeline could not complete."
            return jsonify({
                "success": False,
                "message": message,
                "pipeline": result,
            }), 422

        selected_questions = result.get("selected_questions")
        if not isinstance(selected_questions, dict):
            raise RuntimeError("The generated paper preview is unavailable.")
        generated_count = sum(
            len(section.get("questions", []))
            for section in selected_questions.get("sections", {}).values()
        )
        generation_result = result.get("generation_result")
        persistence = (
            generation_result.get("persistence", {})
            if isinstance(generation_result, dict)
            else {}
        )
        if (
            persistence.get("status") != "SAVED"
            or persistence.get("total_questions") != generated_count
            or persistence.get("mapped_questions") != generated_count
            or persistence.get("usage_records") != generated_count
            or persistence.get("generation_log_records") != 1
            or persistence.get("generation_id") is None
        ):
            raise RuntimeError(
                "PERSISTENCE_ERROR: Paper generation cannot succeed without "
                "a complete saved paper, mappings, usage history, and generation log."
            )
        response = jsonify({
            "success": True,
            "paper_information": selected_questions.get("paper_information", {}),
            "sections": selected_questions.get("sections", {}),
            "variation": (
                generation_result.get("variation", {})
                if isinstance(generation_result, dict)
                else {}
            ),
            "generation_milliseconds": round((time.perf_counter() - started_at) * 1000),
        })
        response.call_on_close(lambda: shutil.rmtree(output_dir, ignore_errors=True))
        return response
    except Exception as error:
        if "output_dir" in locals():
            shutil.rmtree(output_dir, ignore_errors=True)
        return jsonify({"success": False, "error": str(error)}), 500


@generation_bp.route("/api/download-reviewed-paper", methods=["POST"])
@require_supabase_roles("admin", "faculty")
def download_reviewed_paper():
    reviewed_paper = request.get_json(silent=True)
    if not isinstance(reviewed_paper, dict):
        return jsonify({"success": False, "error": "A reviewed paper object is required."}), 400

    if not _PIPELINE_ROOT.is_dir():
        return jsonify({"success": False, "error": "The paper formatter is unavailable."}), 500

    root = str(_PIPELINE_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)

    output_dir = None
    try:
        from Question_Paper_Formatter.docx_generator import generate_docx
        from Question_Paper_Formatter.paper_formatter import validate_and_format_paper

        is_valid, errors, formatted_paper = validate_and_format_paper(reviewed_paper)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": "The reviewed paper is invalid.",
                "details": errors,
            }), 400

        output_dir = Path(tempfile.mkdtemp(prefix="eduquest-reviewed-paper-"))
        docx_path = output_dir / "EduQuest_Reviewed_Question_Paper.docx"
        generate_docx(formatted_paper, str(docx_path))
        response = send_file(
            docx_path,
            as_attachment=True,
            download_name="EduQuest_Reviewed_Question_Paper.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response.call_on_close(lambda: shutil.rmtree(output_dir, ignore_errors=True))
        return response
    except Exception as error:
        if output_dir:
            shutil.rmtree(output_dir, ignore_errors=True)
        return jsonify({"success": False, "error": str(error)}), 500
