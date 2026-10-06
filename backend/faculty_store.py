import json
import os

FACULTY_FILE = "faculty_data.json"

def get_faculty():
    if not os.path.exists(FACULTY_FILE):
        default_data = [
            {'id': 1, 'name': 'Dr. Sarah Connor', 'course': 'Computer Technology', 'role': 'Paper Setter', 'status': 'Active'},
            {'id': 2, 'name': 'Prof. Alan Turing', 'course': 'Computer Technology', 'role': 'Moderator', 'status': 'Reviewing'},
            {'id': 3, 'name': 'Dr. Ada Lovelace', 'course': 'Information Technology', 'role': 'Admin', 'status': 'Active'},
            {'id': 4, 'name': 'Prof. Grace Hopper', 'course': 'Information Technology', 'role': 'Paper Setter', 'status': 'Active'},
            {'id': 5, 'name': 'Dr. Ananya Rao', 'course': 'ENTC', 'role': 'Moderator', 'status': 'Reviewing'},
            {'id': 6, 'name': 'Prof. Vikram Deshmukh', 'course': 'ENTC', 'role': 'Paper Setter', 'status': 'Active'},
            {'id': 7, 'name': 'Dr. Meera Joshi', 'course': 'Mechanical', 'role': 'Admin', 'status': 'Offline'},
            {'id': 8, 'name': 'Prof. Arjun Kulkarni', 'course': 'Mechanical', 'role': 'Paper Setter', 'status': 'Active'}
        ]
        save_faculty(default_data)
        return default_data
    with open(FACULTY_FILE, "r") as f:
        return json.load(f)

def save_faculty(data):
    with open(FACULTY_FILE, "w") as f:
        json.dump(data, f)
