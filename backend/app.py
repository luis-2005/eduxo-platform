from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import random
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Gerar dados sintéticos simples
def generate_students(n=100):
    students = []
    classes = ['1A', '1B', '2A', '2B', '3A', '3B']
    
    for i in range(n):
        attendance = random.uniform(40, 100)
        grades = random.uniform(3, 10)
        participation = random.uniform(30, 100)
        absences = int((100 - attendance) * 0.4)
        socioeconomic = random.uniform(1, 5)
        
        risk_score = (
            (100 - attendance) * 0.3 +
            (10 - grades) * 10 * 0.25 +
            (100 - participation) * 0.2 +
            absences * 0.15 +
            (6 - socioeconomic) * 4 * 0.1
        )
        
        risk_level = 'Alto' if risk_score > 60 else 'Médio' if risk_score > 35 else 'Baixo'
        
        students.append({
            'id': i + 1,
            'name': f'Aluno {i + 1}',
            'class': random.choice(classes),
            'attendance': round(attendance, 1),
            'grades': round(grades, 1),
            'participation': round(participation, 1),
            'absences': absences,
            'socioeconomic': round(socioeconomic, 1),
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level
        })
    
    return students

# Dados em memória
STUDENTS = generate_students(100)

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/students')
def get_students():
    class_filter = request.args.get('class')
    risk_filter = request.args.get('risk')
    
    filtered = STUDENTS.copy()
    
    if class_filter and class_filter != 'Todas':
        filtered = [s for s in filtered if s['class'] == class_filter]
    
    if risk_filter and risk_filter != 'Todos':
        filtered = [s for s in filtered if s['risk_level'] == risk_filter]
    
    return jsonify(filtered)

@app.route('/api/stats')
def get_stats():
    high = len([s for s in STUDENTS if s['risk_level'] == 'Alto'])
    medium = len([s for s in STUDENTS if s['risk_level'] == 'Médio'])
    low = len([s for s in STUDENTS if s['risk_level'] == 'Baixo'])
    
    return jsonify({
        'total_students': len(STUDENTS),
        'high_risk': high,
        'medium_risk': medium,
        'low_risk': low,
        'avg_attendance': round(sum(s['attendance'] for s in STUDENTS) / len(STUDENTS), 1),
        'avg_grades': round(sum(s['grades'] for s in STUDENTS) / len(STUDENTS), 1)
    })

@app.route('/api/classes')
def get_classes():
    classes_data = {}
    
    for student in STUDENTS:
        cls = student['class']
        if cls not in classes_data:
            classes_data[cls] = []
        classes_data[cls].append(student)
    
    result = []
    for cls, students in classes_data.items():
        result.append({
            'class': cls,
            'total_students': len(students),
            'high_risk': len([s for s in students if s['risk_level'] == 'Alto']),
            'avg_risk': round(sum(s['risk_score'] for s in students) / len(students), 1)
        })
    
    return jsonify(sorted(result, key=lambda x: x['class']))

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 78890))
    app.run(host='0.0.0.0', port=port)