from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Gerador de dados sintéticos
def generate_student_data(n_students=100):
    np.random.seed(42)
    
    names = ['Ana Silva', 'Bruno Costa', 'Carlos Souza', 'Diana Lima', 'Eduardo Santos', 
             'Fernanda Oliveira', 'Gabriel Alves', 'Helena Martins', 'Igor Pereira', 
             'Julia Rodrigues', 'Lucas Ferreira', 'Maria Santos', 'Nicolas Carvalho', 
             'Olivia Mendes', 'Pedro Ribeiro']
    
    classes = ['1A', '1B', '2A', '2B', '3A', '3B']
    
    data = []
    for i in range(n_students):
        attendance = np.random.uniform(40, 100)
        grades = np.random.uniform(3, 10)
        participation = np.random.uniform(30, 100)
        absences = int((100 - attendance) * 0.4)
        socioeconomic = np.random.uniform(1, 5)
        
        # Score de risco (0-100)
        risk_score = (
            (100 - attendance) * 0.3 +
            (10 - grades) * 10 * 0.25 +
            (100 - participation) * 0.2 +
            absences * 0.15 +
            (6 - socioeconomic) * 4 * 0.1
        )
        
        # Classificação
        if risk_score > 60:
            risk_level = 'Alto'
            evasion = 1
        elif risk_score > 35:
            risk_level = 'Médio'
            evasion = np.random.choice([0, 1], p=[0.7, 0.3])
        else:
            risk_level = 'Baixo'
            evasion = 0
        
        data.append({
            'id': i + 1,
            'name': f"{np.random.choice(names)} {i+1}",
            'class': np.random.choice(classes),
            'attendance': round(attendance, 1),
            'grades': round(grades, 1),
            'participation': round(participation, 1),
            'absences': absences,
            'socioeconomic': round(socioeconomic, 1),
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'evasion': evasion,
            'last_update': datetime.now().strftime('%Y-%m-%d')
        })
    
    return pd.DataFrame(data)

# Treinar modelo ML
def train_model():
    df = generate_student_data(500)
    
    features = ['attendance', 'grades', 'participation', 'absences', 'socioeconomic']
    X = df[features]
    y = df['evasion']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    
    return model, scaler

# Inicializar modelo
print("🚀 Treinando modelo de Machine Learning...")
model, scaler = train_model()
print("✅ Modelo treinado com sucesso!")

# Gerar dados iniciais
students_df = generate_student_data(100)

@app.route('/')
def home():
    return jsonify({
        'message': 'EDUXO API - Plataforma Inteligente de Prevenção de Evasão Escolar',
        'version': '1.0.0',
        'endpoints': {
            '/api/students': 'GET - Lista todos os alunos',
            '/api/students/<id>': 'GET - Detalhes de um aluno',
            '/api/predict': 'POST - Predição de risco para novos dados',
            '/api/stats': 'GET - Estatísticas gerais',
            '/api/classes': 'GET - Análise por turma'
        }
    })

@app.route('/api/students', methods=['GET'])
def get_students():
    class_filter = request.args.get('class')
    risk_filter = request.args.get('risk')
    
    filtered_df = students_df.copy()
    
    if class_filter and class_filter != 'Todas':
        filtered_df = filtered_df[filtered_df['class'] == class_filter]
    
    if risk_filter and risk_filter != 'Todos':
        filtered_df = filtered_df[filtered_df['risk_level'] == risk_filter]
    
    return jsonify(filtered_df.to_dict('records'))

@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = students_df[students_df['id'] == student_id]
    
    if student.empty:
        return jsonify({'error': 'Aluno não encontrado'}), 404
    
    return jsonify(student.to_dict('records')[0])

@app.route('/api/predict', methods=['POST'])
def predict_risk():
    data = request.json
    
    try:
        features = np.array([[
            data['attendance'],
            data['grades'],
            data['participation'],
            data['absences'],
            data['socioeconomic']
        ]])
        
        features_scaled = scaler.transform(features)
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0]
        
        # Calcular risk_score
        risk_score = (
            (100 - data['attendance']) * 0.3 +
            (10 - data['grades']) * 10 * 0.25 +
            (100 - data['participation']) * 0.2 +
            data['absences'] * 0.15 +
            (6 - data['socioeconomic']) * 4 * 0.1
        )
        
        risk_level = 'Alto' if risk_score > 60 else 'Médio' if risk_score > 35 else 'Baixo'
        
        return jsonify({
            'prediction': int(prediction),
            'probability_evasion': round(float(probability[1]) * 100, 2),
            'probability_permanence': round(float(probability[0]) * 100, 2),
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'recommendation': get_recommendation(risk_level)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'total_students': len(students_df),
        'high_risk': len(students_df[students_df['risk_level'] == 'Alto']),
        'medium_risk': len(students_df[students_df['risk_level'] == 'Médio']),
        'low_risk': len(students_df[students_df['risk_level'] == 'Baixo']),
        'avg_attendance': round(students_df['attendance'].mean(), 1),
        'avg_grades': round(students_df['grades'].mean(), 1),
        'avg_risk_score': round(students_df['risk_score'].mean(), 1)
    })

@app.route('/api/classes', methods=['GET'])
def get_classes_analysis():
    class_stats = []
    
    for class_name in students_df['class'].unique():
        class_data = students_df[students_df['class'] == class_name]
        
        class_stats.append({
            'class': class_name,
            'total_students': len(class_data),
            'high_risk': len(class_data[class_data['risk_level'] == 'Alto']),
            'avg_risk': round(class_data['risk_score'].mean(), 1),
            'avg_attendance': round(class_data['attendance'].mean(), 1),
            'avg_grades': round(class_data['grades'].mean(), 1)
        })
    
    return jsonify(sorted(class_stats, key=lambda x: x['class']))

def get_recommendation(risk_level):
    recommendations = {
        'Alto': 'Intervenção urgente necessária. Contatar família e equipe pedagógica.',
        'Médio': 'Monitoramento constante. Oferecer apoio acadêmico e atividades extras.',
        'Baixo': 'Continuar acompanhamento regular. Manter engajamento positivo.'
    }
    return recommendations.get(risk_level, '')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7788))
    app.run(host='0.0.0.0', port=port, debug=False)