from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Configuração do banco de dados
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost/evasao_escolar')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

def get_db_connection():
    """Cria conexão com o banco de dados"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Tabela de alunos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            class VARCHAR(10) NOT NULL,
            attendance DECIMAL(5,2) DEFAULT 0,
            grades DECIMAL(5,2) DEFAULT 0,
            participation DECIMAL(5,2) DEFAULT 0,
            absences INTEGER DEFAULT 0,
            socioeconomic DECIMAL(3,1) DEFAULT 3.0,
            risk_score DECIMAL(5,2) DEFAULT 0,
            risk_level VARCHAR(20) DEFAULT 'Baixo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de histórico de alertas
    cur.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            alert_type VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            severity VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Tabela de intervenções
    cur.execute('''
        CREATE TABLE IF NOT EXISTS interventions (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            intervention_type VARCHAR(100) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'Pendente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    # Tabela de evolução mensal
    cur.execute('''
        CREATE TABLE IF NOT EXISTS monthly_stats (
            id SERIAL PRIMARY KEY,
            month DATE NOT NULL,
            total_students INTEGER,
            high_risk INTEGER,
            medium_risk INTEGER,
            low_risk INTEGER,
            avg_attendance DECIMAL(5,2),
            avg_grades DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

def populate_initial_data():
    """Popula dados iniciais se o banco estiver vazio"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) as count FROM students')
    count = cur.fetchone()['count']
    
    if count == 0:
        classes = ['1A', '1B', '2A', '2B', '3A', '3B']
        
        for i in range(100):
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
            
            cur.execute('''
                INSERT INTO students 
                (name, class, attendance, grades, participation, absences, socioeconomic, risk_score, risk_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                f'Aluno {i + 1}',
                random.choice(classes),
                round(attendance, 2),
                round(grades, 2),
                round(participation, 2),
                absences,
                round(socioeconomic, 1),
                round(risk_score, 2),
                risk_level
            ))
            
            # Criar alertas para alunos de alto risco
            if risk_level == 'Alto':
                cur.execute('''
                    INSERT INTO alerts (student_id, alert_type, message, severity)
                    VALUES (%s, %s, %s, %s)
                ''', (
                    i + 1,
                    'Risco de Evasão',
                    f'Aluno {i + 1} apresenta alto risco de evasão escolar',
                    'Alta'
                ))
        
        # Estatísticas mensais dos últimos 6 meses
        for month_offset in range(6, 0, -1):
            month_date = datetime.now() - timedelta(days=30 * month_offset)
            cur.execute('''
                INSERT INTO monthly_stats 
                (month, total_students, high_risk, medium_risk, low_risk, avg_attendance, avg_grades)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                month_date.date(),
                100,
                random.randint(15, 30),
                random.randint(30, 45),
                random.randint(25, 40),
                random.uniform(75, 85),
                random.uniform(6.5, 7.5)
            ))
        
        conn.commit()
    
    cur.close()
    conn.close()

# Inicializar banco ao iniciar
try:
    init_db()
    populate_initial_data()
except Exception as e:
    print(f"Erro ao inicializar banco: {e}")

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/students', methods=['GET'])
def get_students():
    """Retorna lista de alunos com filtros"""
    class_filter = request.args.get('class')
    risk_filter = request.args.get('risk')
    search = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = 'SELECT * FROM students WHERE 1=1'
    params = []
    
    if class_filter and class_filter != 'Todas':
        query += ' AND class = %s'
        params.append(class_filter)
    
    if risk_filter and risk_filter != 'Todos':
        query += ' AND risk_level = %s'
        params.append(risk_filter)
    
    if search:
        query += ' AND name ILIKE %s'
        params.append(f'%{search}%')
    
    query += ' ORDER BY risk_score DESC'
    
    cur.execute(query, params)
    students = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify(students)

@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Retorna detalhes de um aluno específico"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM students WHERE id = %s', (student_id,))
    student = cur.fetchone()
    
    if not student:
        return jsonify({'error': 'Aluno não encontrado'}), 404
    
    # Buscar alertas do aluno
    cur.execute('''
        SELECT * FROM alerts 
        WHERE student_id = %s 
        ORDER BY created_at DESC LIMIT 10
    ''', (student_id,))
    alerts = cur.fetchall()
    
    # Buscar intervenções do aluno
    cur.execute('''
        SELECT * FROM interventions 
        WHERE student_id = %s 
        ORDER BY created_at DESC
    ''', (student_id,))
    interventions = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'student': student,
        'alerts': alerts,
        'interventions': interventions
    })

@app.route('/api/students', methods=['POST'])
def create_student():
    """Cria um novo aluno"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO students 
        (name, class, attendance, grades, participation, absences, socioeconomic, risk_score, risk_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (
        data['name'],
        data['class'],
        data.get('attendance', 0),
        data.get('grades', 0),
        data.get('participation', 0),
        data.get('absences', 0),
        data.get('socioeconomic', 3.0),
        data.get('risk_score', 0),
        data.get('risk_level', 'Baixo')
    ))
    
    student_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'id': student_id, 'message': 'Aluno criado com sucesso'}), 201

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Atualiza dados de um aluno"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Recalcular risk_score se dados relevantes mudaram
    if any(k in data for k in ['attendance', 'grades', 'participation', 'absences', 'socioeconomic']):
        attendance = data.get('attendance', 0)
        grades = data.get('grades', 0)
        participation = data.get('participation', 0)
        absences = data.get('absences', 0)
        socioeconomic = data.get('socioeconomic', 3.0)
        
        risk_score = (
            (100 - attendance) * 0.3 +
            (10 - grades) * 10 * 0.25 +
            (100 - participation) * 0.2 +
            absences * 0.15 +
            (6 - socioeconomic) * 4 * 0.1
        )
        
        risk_level = 'Alto' if risk_score > 60 else 'Médio' if risk_score > 35 else 'Baixo'
        data['risk_score'] = round(risk_score, 2)
        data['risk_level'] = risk_level
    
    # Construir query de atualização dinamicamente
    fields = []
    values = []
    for key, value in data.items():
        if key != 'id':
            fields.append(f"{key} = %s")
            values.append(value)
    
    values.append(student_id)
    
    cur.execute(f'''
        UPDATE students 
        SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    ''', values)
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'Aluno atualizado com sucesso'})

@app.route('/api/stats')
def get_stats():
    """Retorna estatísticas gerais"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT 
            COUNT(*) as total_students,
            SUM(CASE WHEN risk_level = 'Alto' THEN 1 ELSE 0 END) as high_risk,
            SUM(CASE WHEN risk_level = 'Médio' THEN 1 ELSE 0 END) as medium_risk,
            SUM(CASE WHEN risk_level = 'Baixo' THEN 1 ELSE 0 END) as low_risk,
            AVG(attendance) as avg_attendance,
            AVG(grades) as avg_grades,
            AVG(risk_score) as avg_risk_score
        FROM students
    ''')
    
    stats = cur.fetchone()
    
    # Alertas não resolvidos
    cur.execute('SELECT COUNT(*) as count FROM alerts WHERE resolved = FALSE')
    unresolved_alerts = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    
    return jsonify({
        'total_students': stats['total_students'],
        'high_risk': stats['high_risk'],
        'medium_risk': stats['medium_risk'],
        'low_risk': stats['low_risk'],
        'avg_attendance': round(float(stats['avg_attendance'] or 0), 1),
        'avg_grades': round(float(stats['avg_grades'] or 0), 1),
        'avg_risk_score': round(float(stats['avg_risk_score'] or 0), 1),
        'unresolved_alerts': unresolved_alerts
    })

@app.route('/api/classes')
def get_classes():
    """Retorna estatísticas por turma"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT 
            class,
            COUNT(*) as total_students,
            SUM(CASE WHEN risk_level = 'Alto' THEN 1 ELSE 0 END) as high_risk,
            SUM(CASE WHEN risk_level = 'Médio' THEN 1 ELSE 0 END) as medium_risk,
            SUM(CASE WHEN risk_level = 'Baixo' THEN 1 ELSE 0 END) as low_risk,
            AVG(risk_score) as avg_risk,
            AVG(attendance) as avg_attendance,
            AVG(grades) as avg_grades
        FROM students
        GROUP BY class
        ORDER BY class
    ''')
    
    classes = cur.fetchall()
    cur.close()
    conn.close()
    
    result = []
    for cls in classes:
        result.append({
            'class': cls['class'],
            'total_students': cls['total_students'],
            'high_risk': cls['high_risk'],
            'medium_risk': cls['medium_risk'],
            'low_risk': cls['low_risk'],
            'avg_risk': round(float(cls['avg_risk'] or 0), 1),
            'avg_attendance': round(float(cls['avg_attendance'] or 0), 1),
            'avg_grades': round(float(cls['avg_grades'] or 0), 1)
        })
    
    return jsonify(result)

@app.route('/api/trends')
def get_trends():
    """Retorna evolução temporal dos dados"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT * FROM monthly_stats
        ORDER BY month ASC
    ''')
    
    trends = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify(trends)

@app.route('/api/alerts')
def get_alerts():
    """Retorna alertas recentes"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT a.*, s.name as student_name, s.class
        FROM alerts a
        JOIN students s ON a.student_id = s.id
        WHERE a.resolved = FALSE
        ORDER BY a.created_at DESC
        LIMIT 50
    ''')
    
    alerts = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify(alerts)

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Marca um alerta como resolvido"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('UPDATE alerts SET resolved = TRUE WHERE id = %s', (alert_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'Alerta resolvido com sucesso'})

@app.route('/api/interventions', methods=['POST'])
def create_intervention():
    """Cria uma nova intervenção"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO interventions (student_id, intervention_type, description, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (
        data['student_id'],
        data['intervention_type'],
        data.get('description', ''),
        data.get('status', 'Pendente')
    ))
    
    intervention_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'id': intervention_id, 'message': 'Intervenção criada com sucesso'}), 201

@app.route('/health')
def health():
    """Endpoint de health check"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5432))
    app.run(host='0.0.0.0', port=port, debug=False)