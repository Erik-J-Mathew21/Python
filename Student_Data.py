student_data = {
    "id1": {"name": "Erik", "class": "6E", "subject_integration": "english, math, science"}, 
    "id2": {"name": "Henry", "class": "6E", "subject_integration": "english, math, science"}, 
    "id3": {"name": "Tom", "class": "6E", "subject_integration": "english, math, science"}, 
    "id4": {"name": "Adheshwar", "class": "6E", "subject_integration": "english, math, science"}, 
    "id5": {"name": "Henry", "class": "6E", "subject_integration": "english, math, science"}, 
    "id6": {"name": "Ternence", "class": "6E", "subject_integration": "english, math, science"}
}
result = {}
seen_keys = []
for student_id, details in student_data.items():
    unique_key = (details["name"], details["class"], details["subject_integration"])
    if unique_key not in seen_keys:
        seen_keys.append(unique_key)
        result[student_id] = details
for k, v in result.items():
        print(k, ":", v)