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
    """Cria conexão com o banco de dados com tratamento de erro"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"ERRO DE CONEXÃO COM O BANCO DE DADOS: {e}")
        # É crucial que este erro seja propagado para o endpoint /api/init
        raise ConnectionError("Falha ao conectar com o banco de dados. Verifique DATABASE_URL e a disponibilidade do serviço.") from e

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = None
    try:
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
    except Exception as e:
        print(f"ERRO ao inicializar o banco de dados: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def populate_initial_data():
    """Popula dados iniciais se o banco estiver vazio"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT COUNT(*) as count FROM students')
        count = cur.fetchone()['count']
        
        if count == 0:
            print("Populando dados iniciais...")
            # Lista expandida de nomes brasileiros
            nomes_masculinos = [
                'Miguel Silva', 'Davi Santos', 'Gabriel Oliveira', 'Arthur Costa', 'Lucas Souza',
                'Matheus Ferreira', 'Pedro Rodrigues', 'Guilherme Almeida', 'Gustavo Lima', 'Rafael Pereira',
                'Felipe Carvalho', 'Bernardo Ribeiro', 'Enzo Martins', 'Nicolas Araújo', 'João Pedro Dias',
                'Cauã Fernandes', 'Vitor Gomes', 'Eduardo Cardoso', 'Daniel Rocha', 'Henrique Barbosa',
                'Murilo Castro', 'Vinicius Nascimento', 'Samuel Moreira', 'Pietro Pinto', 'João Vitor Monteiro',
                'Leonardo Freitas', 'Caio Duarte', 'Heitor Teixeira', 'Lorenzo Barros', 'Isaac Cavalcanti',
                'Lucca Azevedo', 'Thiago Mendes', 'João Gabriel Correia', 'João Moraes', 'Alexandre Nunes',
                'Bruno Rezende', 'Benício Campos', 'Ryan Cardoso', 'Emanuel Farias', 'Fernando Vieira',
                'Joaquim Ramos', 'André Nogueira', 'Tomás Cunha', 'Francisco Batista', 'Rodrigo Melo',
                'Igor Peixoto', 'Otávio Lopes', 'Augusto Torres', 'Marcelo Santana', 'Fábio Cruz',
                'Benjamin Lima', 'Elias Santos', 'Theo Oliveira', 'Gael Costa', 'Noah Souza',
                'Luan Ferreira', 'Breno Rodrigues', 'Ian Almeida', 'Caleb Lima', 'Levi Pereira',
                'Raul Carvalho', 'Diego Ribeiro', 'Yuri Martins', 'Renan Araújo', 'Erick Dias',
                'Victor Fernandes', 'Bryan Gomes', 'Kauã Cardoso', 'Arthur Rocha', 'Luiz Barbosa',
                'Antônio Castro', 'Benício Nascimento', 'Erick Moreira', 'Felipe Pinto', 'Giovanni Monteiro',
                'Hugo Freitas', 'Israel Duarte', 'Júlio Teixeira', 'Kevin Barros', 'Léo Cavalcanti',
                'Marcos Azevedo', 'Nathan Mendes', 'Oliver Correia', 'Paulo Moraes', 'Quentin Nunes',
                'Rian Rezende', 'Saulo Campos', 'Téo Cardoso', 'Uriel Farias', 'Wallace Vieira',
                'Xavier Ramos', 'Yago Nogueira', 'Zion Cunha', 'Alan Batista', 'Bento Melo',
                'César Peixoto', 'Davi Lopes', 'Erick Torres', 'Fábio Santana', 'Gael Cruz'
            ]
            
            nomes_femininos = [
                'Sophia Oliveira', 'Alice Santos', 'Julia Silva', 'Isabella Costa', 'Manuela Souza',
                'Laura Ferreira', 'Luiza Rodrigues', 'Valentina Almeida', 'Giovanna Lima', 'Maria Eduarda Pereira',
                'Helena Carvalho', 'Beatriz Ribeiro', 'Maria Luiza Martins', 'Lara Araújo', 'Mariana Dias',
                'Nicole Fernandes', 'Rafaela Gomes', 'Heloísa Cardoso', 'Isadora Rocha', 'Lívia Barbosa',
                'Maria Clara Castro', 'Ana Clara Nascimento', 'Lorena Moreira', 'Gabriela Pinto', 'Yasmin Monteiro',
                'Isabelly Freitas', 'Sarah Duarte', 'Ana Julia Teixeira', 'Letícia Barros', 'Ana Luiza Cavalcanti',
                'Melissa Azevedo', 'Marina Mendes', 'Clara Correia', 'Cecília Moraes', 'Esther Nunes',
                'Emanuelly Rezende', 'Rebeca Campos', 'Ana Beatriz Cardoso', 'Lavínia Farias', 'Vitória Vieira',
                'Bianca Ramos', 'Catarina Nogueira', 'Larissa Cunha', 'Maria Fernanda Batista', 'Fernanda Melo',
                'Amanda Peixoto', 'Alícia Lopes', 'Carolina Torres', 'Agatha Santana', 'Gabrielly Cruz',
                'Elisa Lima', 'Maya Santos', 'Ayla Oliveira', 'Aurora Costa', 'Stella Souza',
                'Pietra Ferreira', 'Milena Rodrigues', 'Liz Almeida', 'Antonella Lima', 'Maitê Pereira',
                'Eliza Carvalho', 'Eloá Ribeiro', 'Maria Alice Martins', 'Luna Araújo', 'Duda Dias',
                'Bella Fernandes', 'Sophie Gomes', 'Aurora Cardoso', 'Maria Vitória Rocha', 'Olívia Barbosa',
                'Maria Helena Castro', 'Helena Nascimento', 'Laís Moreira', 'Maria Cecília Pinto', 'Brenda Monteiro',
                'Evelyn Freitas', 'Hadassa Duarte', 'Maria Júlia Teixeira', 'Alana Barros', 'Elisa Cavalcanti',
                'Jade Azevedo', 'Joana Mendes', 'Lorena Correia', 'Maria Luísa Moraes', 'Nina Nunes',
                'Pérola Rezende', 'Stella Campos', 'Valentina Cardoso', 'Yasmin Farias', 'Zoe Vieira',
                'Ana Ramos', 'Bárbara Nogueira', 'Camila Cunha', 'Diana Batista', 'Emilly Melo',
                'Flávia Peixoto', 'Gisele Lopes', 'Ingrid Torres', 'Jéssica Santana', 'Kelly Cruz'
            ]
            
            todos_nomes = nomes_masculinos + nomes_femininos
            random.shuffle(todos_nomes)
            # Garantir que temos pelo menos 200 nomes únicos
            todos_nomes = todos_nomes[:200]
            
            classes = ['1A', '1B', '1C', '2A', '2B', '2C', '3A', '3B', '3C']
            
            # Criar 200 alunos com diferentes perfis de risco
            for i in range(200):
                nome = todos_nomes[i]
                
                # 20% dos alunos em situação CRÍTICA (Alto Risco) - Aumentado para garantir a visualização
                if i < 40: # 20% de 200 = 40 alunos
                    attendance = random.uniform(30, 55)
                    grades = random.uniform(2.5, 4.5)
                    participation = random.uniform(20, 45)
                    absences = random.randint(20, 40)
                    socioeconomic = random.uniform(1.0, 2.0)
                
                # 30% dos alunos em situação de RISCO MÉDIO
                elif i < 100: # 30% de 200 = 60 alunos (40 a 99)
                    attendance = random.uniform(55, 75)
                    grades = random.uniform(4.5, 6.5)
                    participation = random.uniform(45, 65)
                    absences = random.randint(10, 20)
                    socioeconomic = random.uniform(2.0, 3.5)
                
                # 50% dos alunos em situação NORMAL (Baixo Risco)
                else: # 50% de 200 = 100 alunos (100 a 199)
                    attendance = random.uniform(75, 98)
                    grades = random.uniform(6.5, 10)
                    participation = random.uniform(65, 95)
                    absences = random.randint(0, 10)
                    socioeconomic = random.uniform(3.0, 5.0)
                
                # Cálculo do score de risco
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
                    RETURNING id
                ''', (
                    nome,
                    random.choice(classes),
                    round(attendance, 2),
                    round(grades, 2),
                    round(participation, 2),
                    absences,
                    round(socioeconomic, 1),
                    round(risk_score, 2),
                    risk_level
                ))
                
                student_id = cur.fetchone()['id']
                
                # Criar alertas para alunos de alto risco
                if risk_level == 'Alto':
                    alert_types = [
                        ('Frequência Crítica', f'{nome} tem frequência de apenas {attendance:.1f}%', 'Alta'),
                        ('Notas Baixas', f'{nome} está com média {grades:.1f}', 'Alta'),
                        ('Risco de Evasão', f'{nome} apresenta múltiplos indicadores de risco', 'Alta')
                    ]
                    
                    for alert_type, message, severity in alert_types[:random.randint(1, 2)]:
                        cur.execute('''
                            INSERT INTO alerts (student_id, alert_type, message, severity)
                            VALUES (%s, %s, %s, %s)
                        ''', (student_id, alert_type, message, severity))
            
            # Criar dados de evolução mensal (últimos 6 meses)
            for i in range(6):
                month = datetime.now() - timedelta(days=30*i)
                
                # Simular tendência de melhora ao longo do tempo
                high_risk = random.randint(35 - i*2, 45 - i*2)
                medium_risk = random.randint(55 - i, 65 - i)
                low_risk = 200 - high_risk - medium_risk
                
                cur.execute('''
                    INSERT INTO monthly_stats 
                    (month, total_students, high_risk, medium_risk, low_risk, avg_attendance, avg_grades)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    month.date(),
                    200,
                    high_risk,
                    medium_risk,
                    low_risk,
                    random.uniform(70, 80),
                    random.uniform(6, 7.5)
                ))
            
            conn.commit()
            print("Dados iniciais populados com sucesso.")
        else:
            print(f"Banco de dados já contém {count} alunos. Pulando a população de dados.")
        
        cur.close()
    except Exception as e:
        print(f"ERRO ao popular dados iniciais: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# Rotas da API
@app.route('/')
def serve_frontend():
    """Serve o frontend"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/init', methods=['POST'])
def initialize():
    """Inicializa o banco de dados"""
    try:
        init_db()
        populate_initial_data()
        return jsonify({'message': 'Banco de dados inicializado com sucesso', 'status': 'ok'})
    except ConnectionError as ce:
        return jsonify({'error': str(ce), 'status': 'connection_error'}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'initialization_error'}), 500

@app.route('/api/students')
def get_students():
    """Retorna lista de alunos com filtros opcionais"""
    risk_level = request.args.get('risk_level')
    class_name = request.args.get('class')
    search = request.args.get('search')
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = 'SELECT * FROM students WHERE 1=1'
        params = []
        
        if risk_level:
            query += ' AND risk_level = %s'
            params.append(risk_level)
        
        if class_name:
            query += ' AND class = %s'
            params.append(class_name)
        
        if search:
            query += ' AND LOWER(name) LIKE %s'
            params.append(f'%{search.lower()}%')
        
        query += ' ORDER BY risk_score DESC'
        
        cur.execute(query, params)
        students = cur.fetchall()
        
        cur.close()
        return jsonify(students)
    except ConnectionError as ce:
        return jsonify({'error': str(ce), 'status': 'connection_error'}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'query_error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/students/<int:student_id>')
def get_student(student_id):
    """Retorna detalhes de um aluno específico"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Dados do aluno
        cur.execute('SELECT * FROM students WHERE id = %s', (student_id,))
        student = cur.fetchone()
        
        if not student:
            return jsonify({'error': 'Aluno não encontrado'}), 404
        
        # Alertas do aluno
        cur.execute('''
            SELECT * FROM alerts 
            WHERE student_id = %s 
            ORDER BY created_at DESC
        ''', (student_id,))
        alerts = cur.fetchall()
        
        # Intervenções do aluno
        cur.execute('''
            SELECT * FROM interventions 
            WHERE student_id = %s 
            ORDER BY created_at DESC
        ''', (student_id,))
        interventions = cur.fetchall()
        
        cur.close()
        
        return jsonify({
            'student': student,
            'alerts': alerts,
            'interventions': interventions
        })
    except ConnectionError as ce:
        return jsonify({'error': str(ce), 'status': 'connection_error'}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'query_error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Atualiza dados de um aluno"""
    data = request.json
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Recalcular risk_score se os dados mudaram
        attendance = data.get('attendance')
        grades = data.get('grades')
        participation = data.get('participation')
        absences = data.get('absences')
        socioeconomic = data.get('socioeconomic')
        
        if all([attendance, grades, participation, absences, socioeconomic]):
            risk_score = (
                (100 - attendance) * 0.3 +
                (10 - grades) * 10 * 0.25 +
                (100 - participation) * 0.2 +
                absences * 0.15 +
                (6 - socioeconomic) * 4 * 0.1
            )
            risk_level = 'Alto' if risk_score > 60 else 'Médio' if risk_score > 35 else 'Baixo'
            
            cur.execute('''
                UPDATE students 
                SET attendance = %s, grades = %s, participation = %s, 
                    absences = %s, socioeconomic = %s, risk_score = %s, 
                    risk_level = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (attendance, grades, participation, absences, socioeconomic, 
                  round(risk_score, 2), risk_level, student_id))
        
        conn.commit()
        cur.close()
        return jsonify({'message': 'Aluno atualizado com sucesso'})
    except ConnectionError as ce:
        return jsonify({'error': str(ce), 'status': 'connection_error'}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e), 'status': 'update_error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/dashboard')
def get_dashboard():
    """Retorna dados agregados para o dashboard"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Estatísticas Gerais (stats)
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
        
        cur.execute('SELECT COUNT(*) as count FROM alerts WHERE resolved = FALSE')
        unresolved_alerts = cur.fetchone()['count']
        
        stats_data = {
            'total_students': stats['total_students'],
            'high_risk': stats['high_risk'],
            'medium_risk': stats['medium_risk'],
            'low_risk': stats['low_risk'],
            'avg_attendance': round(float(stats['avg_attendance'] or 0), 1),
            'avg_grades': round(float(stats['avg_grades'] or 0), 1),
            'avg_risk_score': round(float(stats['avg_risk_score'] or 0), 1),
            'unresolved_alerts': unresolved_alerts
        }
        
        # 2. Estatísticas por Turma (classes)
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
        classes_raw = cur.fetchall()
        
        classes_data = []
        for cls in classes_raw:
            classes_data.append({
                'class': cls['class'],
                'total_students': cls['total_students'],
                'high_risk': cls['high_risk'],
                'medium_risk': cls['medium_risk'],
                'low_risk': cls['low_risk'],
                'avg_risk': round(float(cls['avg_risk'] or 0), 1),
                'avg_attendance': round(float(cls['avg_attendance'] or 0), 1),
                'avg_grades': round(float(cls['avg_grades'] or 0), 1)
            })
            
        # 3. Evolução Temporal (trends)
        cur.execute('''
            SELECT * FROM monthly_stats
            ORDER BY month ASC
        ''')
        trends_data = cur.fetchall()
        
        cur.close()
        
        return jsonify({
            'stats': stats_data,
            'classes': classes_data,
            'trends': trends_data
        })
    except ConnectionError as ce:
        return jsonify({'error': str(ce), 'status': 'connection_error'}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'query_error'}), 500
    finally:
        if conn:
            conn.close()
    
@app.route('/api/alerts')
def get_alerts():
    """Retorna alertas recentes"""
    conn = None
    try:
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
        return jsonify(alerts)
    except ConnectionError as ce:
        return jsonify({'error': str(ce), 'status': 'connection_error'}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'query_error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Marca um alerta como resolvido"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('UPDATE alerts SET resolved = TRUE WHERE id = %s', (alert_id,))
        conn.commit()
        cur.close()
        return jsonify({'message': 'Alerta resolvido com sucesso'})
    except ConnectionError as ce:
        return jsonify({'error': str(ce), 'status': 'connection_error'}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e), 'status': 'update_error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/interventions', methods=['POST'])
def create_intervention():
    """Cria uma nova intervenção"""
    data = request.json
    
    conn = None
    try:
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
        return jsonify({'id': intervention_id, 'message': 'Intervenção criada com sucesso'}), 201
    except ConnectionError as ce:
        return jsonify({'error': str(ce), 'status': 'connection_error'}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e), 'status': 'insert_error'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/health')
def health():
    """Endpoint de health check"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
