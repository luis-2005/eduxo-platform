import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { AlertTriangle, TrendingUp, Users, BookOpen, AlertCircle, CheckCircle, Download, RefreshCw, Search, Calculator } from 'lucide-react';

const EduxoDashboard = () => {
  const [students, setStudents] = useState([]);
  const [stats, setStats] = useState(null);
  const [classesAnalysis, setClassesAnalysis] = useState([]);
  const [selectedClass, setSelectedClass] = useState('Todas');
  const [filterRisk, setFilterRisk] = useState('Todos');
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showPredictor, setShowPredictor] = useState(false);
  const [predictionForm, setPredictionForm] = useState({
    attendance: 80,
    grades: 7,
    participation: 75,
    absences: 5,
    socioeconomic: 3
  });
  const [predictionResult, setPredictionResult] = useState(null);
  
  // URL da API - MUDE AQUI depois do deploy no Render
  const API_URL = 'https://eduxo-api.onrender.com';
  
  useEffect(() => {
    loadData();
  }, [selectedClass, filterRisk]);
  
  const loadData = async () => {
    setLoading(true);
    try {
      // Carregar estudantes
      const studentsRes = await fetch(`${API_URL}/api/students?class=${selectedClass}&risk=${filterRisk}`);
      const studentsData = await studentsRes.json();
      setStudents(studentsData);
      
      // Carregar estatísticas
      const statsRes = await fetch(`${API_URL}/api/stats`);
      const statsData = await statsRes.json();
      setStats(statsData);
      
      // Carregar análise de turmas
      const classesRes = await fetch(`${API_URL}/api/classes`);
      const classesData = await classesRes.json();
      setClassesAnalysis(classesData);
      
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      // Fallback para dados locais
      generateFallbackData();
    }
    setLoading(false);
  };
  
  const generateFallbackData = () => {
    const mockStudents = Array.from({ length: 20 }, (_, i) => ({
      id: i + 1,
      name: `Aluno ${i + 1}`,
      class: ['1A', '1B', '2A'][i % 3],
      attendance: 60 + Math.random() * 40,
      grades: 4 + Math.random() * 6,
      participation: 50 + Math.random() * 50,
      absences: Math.floor(Math.random() * 15),
      risk_score: 20 + Math.random() * 60,
      risk_level: ['Alto', 'Médio', 'Baixo'][i % 3]
    }));
    setStudents(mockStudents);
    setStats({
      total_students: 20,
      high_risk: 7,
      medium_risk: 8,
      low_risk: 5,
      avg_attendance: 75.5,
      avg_grades: 7.2
    });
  };
  
  const handlePredict = async () => {
    try {
      const response = await fetch(`${API_URL}/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(predictionForm)
      });
      const result = await response.json();
      setPredictionResult(result);
    } catch (error) {
      console.error('Erro na predição:', error);
    }
  };
  
  const filteredStudents = students.filter(s => 
    s.name.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  const highRiskCount = stats?.high_risk || 0;
  const mediumRiskCount = stats?.medium_risk || 0;
  const lowRiskCount = stats?.low_risk || 0;
  
  const riskData = [
    { name: 'Baixo', value: lowRiskCount, color: '#10b981' },
    { name: 'Médio', value: mediumRiskCount, color: '#f59e0b' },
    { name: 'Alto', value: highRiskCount, color: '#ef4444' }
  ];
  
  const exportReport = () => {
    const report = `RELATÓRIO EDUXO - ${new Date().toLocaleDateString('pt-BR')}
    
Total de Alunos: ${stats?.total_students || 0}
Alto Risco: ${highRiskCount}
Médio Risco: ${mediumRiskCount}
Baixo Risco: ${lowRiskCount}
Frequência Média: ${stats?.avg_attendance || 0}%
Nota Média: ${stats?.avg_grades || 0}

ALUNOS DE ALTO RISCO:
${filteredStudents.filter(s => s.risk_level === 'Alto').map(s => 
  `- ${s.name} (${s.class}) - Risco: ${s.risk_score}% - Frequência: ${s.attendance}%`
).join('\n')}

Gerado por: EDUXO - Plataforma Inteligente de Prevenção de Evasão Escolar
Desenvolvedores: Luís Lopes & Jonathas Villalba`;
    
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `relatorio_eduxo_${Date.now()}.txt`;
    a.click();
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-2xl">Carregando dados...</div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4 md:p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2 flex items-center gap-3">
              <BookOpen className="text-purple-400" size={40} />
              EDUXO
            </h1>
            <p className="text-purple-300">Plataforma Inteligente de Prevenção de Evasão Escolar</p>
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => setShowPredictor(!showPredictor)}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
            >
              <Calculator size={20} />
              Preditor ML
            </button>
            <button 
              onClick={loadData}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition"
            >
              <RefreshCw size={20} />
              Atualizar
            </button>
            <button 
              onClick={exportReport}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition"
            >
              <Download size={20} />
              Exportar
            </button>
          </div>
        </div>
      </div>
      
      {/* Preditor ML */}
      {showPredictor && (
        <div className="bg-slate-800 rounded-xl p-6 mb-6 shadow-xl border-2 border-purple-500">
          <h3 className="text-white text-xl font-semibold mb-4">🤖 Preditor de Risco com Machine Learning</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="text-white text-sm mb-1 block">Frequência (%)</label>
              <input 
                type="number" 
                value={predictionForm.attendance}
                onChange={(e) => setPredictionForm({...predictionForm, attendance: parseFloat(e.target.value)})}
                className="w-full bg-slate-700 text-white px-3 py-2 rounded"
              />
            </div>
            <div>
              <label className="text-white text-sm mb-1 block">Nota Média (0-10)</label>
              <input 
                type="number" 
                value={predictionForm.grades}
                onChange={(e) => setPredictionForm({...predictionForm, grades: parseFloat(e.target.value)})}
                className="w-full bg-slate-700 text-white px-3 py-2 rounded"
              />
            </div>
            <div>
              <label className="text-white text-sm mb-1 block">Participação (%)</label>
              <input 
                type="number" 
                value={predictionForm.participation}
                onChange={(e) => setPredictionForm({...predictionForm, participation: parseFloat(e.target.value)})}
                className="w-full bg-slate-700 text-white px-3 py-2 rounded"
              />
            </div>
            <div>
              <label className="text-white text-sm mb-1 block">Faltas</label>
              <input 
                type="number" 
                value={predictionForm.absences}
                onChange={(e) => setPredictionForm({...predictionForm, absences: parseInt(e.target.value)})}
                className="w-full bg-slate-700 text-white px-3 py-2 rounded"
              />
            </div>
            <div>
              <label className="text-white text-sm mb-1 block">Nível Socioeconômico (1-5)</label>
              <input 
                type="number" 
                value={predictionForm.socioeconomic}
                onChange={(e) => setPredictionForm({...predictionForm, socioeconomic: parseFloat(e.target.value)})}
                className="w-full bg-slate-700 text-white px-3 py-2 rounded"
              />
            </div>
            <div className="flex items-end">
              <button 
                onClick={handlePredict}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded transition"
              >
                Calcular Risco
              </button>
            </div>
          </div>
          
          {predictionResult && (
            <div className={`p-4 rounded-lg ${
              predictionResult.risk_level === 'Alto' ? 'bg-red-500/20 border-2 border-red-500' :
              predictionResult.risk_level === 'Médio' ? 'bg-amber-500/20 border-2 border-amber-500' :
              'bg-green-500/20 border-2 border-green-500'
            }`}>
              <h4 className="text-white font-bold text-lg mb-2">Resultado da Predição:</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-white">
                <div>
                  <p className="text-sm opacity-80">Nível de Risco</p>
                  <p className="text-2xl font-bold">{predictionResult.risk_level}</p>
                </div>
                <div>
                  <p className="text-sm opacity-80">Score de Risco</p>
                  <p className="text-2xl font-bold">{predictionResult.risk_score}%</p>
                </div>
                <div>
                  <p className="text-sm opacity-80">Prob. Evasão</p>
                  <p className="text-2xl font-bold">{predictionResult.probability_evasion}%</p>
                </div>
                <div>
                  <p className="text-sm opacity-80">Prob. Permanência</p>
                  <p className="text-2xl font-bold">{predictionResult.probability_permanence}%</p>
                </div>
              </div>
              <p className="text-white mt-3 text-sm">
                <strong>Recomendação:</strong> {predictionResult.recommendation}
              </p>
            </div>
          )}
        </div>
      )}
      
      {/* Filtros e Busca */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="text-white mb-2 block text-sm">Filtrar por Turma</label>
          <select 
            value={selectedClass}
            onChange={(e) => setSelectedClass(e.target.value)}
            className="w-full bg-slate-800 text-white border border-slate-700 rounded-lg px-4 py-2"
          >
            <option>Todas</option>
            <option>1A</option>
            <option>1B</option>
            <option>2A</option>
            <option>2B</option>
            <option>3A</option>
            <option>3B</option>
          </select>
        </div>
        <div>
          <label className="text-white mb-2 block text-sm">Filtrar por Risco</label>
          <select 
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="w-full bg-slate-800 text-white border border-slate-700 rounded-lg px-4 py-2"
          >
            <option>Todos</option>
            <option>Alto</option>
            <option>Médio</option>
            <option>Baixo</option>
          </select>
        </div>
        <div>
          <label className="text-white mb-2 block text-sm">Buscar Aluno</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
            <input 
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Digite o nome..."
              className="w-full bg-slate-800 text-white border border-slate-700 rounded-lg pl-10 pr-4 py-2"
            />
          </div>
        </div>
      </div>
      
      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6 md:mb-8">
        <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-4 md:p-6 text-white shadow-xl transform hover:scale-105 transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-100 text-sm mb-1">Alto Risco</p>
              <p className="text-3xl font-bold">{highRiskCount}</p>
            </div>
            <AlertTriangle size={40} className="text-red-100" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-amber-500 to-amber-600 rounded-xl p-4 md:p-6 text-white shadow-xl transform hover:scale-105 transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-amber-100 text-sm mb-1">Médio Risco</p>
              <p className="text-3xl font-bold">{mediumRiskCount}</p>
            </div>
            <AlertCircle size={40} className="text-amber-100" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-4 md:p-6 text-white shadow-xl transform hover:scale-105 transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm mb-1">Baixo Risco</p>
              <p className="text-3xl font-bold">{lowRiskCount}</p>
            </div>
            <CheckCircle size={40} className="text-green-100" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 md:p-6 text-white shadow-xl transform hover:scale-105 transition">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm mb-1">Total Alunos</p>
              <p className="text-3xl font-bold">{stats?.total_students || 0}</p>
            </div>
            <Users size={40} className="text-blue-100" />
          </div>
        </div>
      </div>
      
      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-slate-800 rounded-xl p-6 shadow-xl">
          <h3 className="text-white text-xl font-semibold mb-4">Distribuição de Risco</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {riskData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        <div className="bg-slate-800 rounded-xl p-6 shadow-xl">
          <h3 className="text-white text-xl font-semibold mb-4">Risco Médio por Turma</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={classesAnalysis}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="class" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="avg_risk" fill="#8b5cf6" name="Risco Médio (%)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Tabela de Alunos */}
      <div className="bg-slate-800 rounded-xl p-6 shadow-xl">
        <h3 className="text-white text-xl font-semibold mb-4">
          Lista de Alunos ({filteredStudents.length})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-purple-300 py-3 px-4">Nome</th>
                <th className="text-purple-300 py-3 px-4">Turma</th>
                <th className="text-purple-300 py-3 px-4">Frequência</th>
                <th className="text-purple-300 py-3 px-4">Nota</th>
                <th className="text-purple-300 py-3 px-4">Risco</th>
                <th className="text-purple-300 py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.slice(0, 15).map(student => (
                <tr key={student.id} className="border-b border-slate-700 hover:bg-slate-700 transition">
                  <td className="text-white py-3 px-4">{student.name}</td>
                  <td className="text-white py-3 px-4">{student.class}</td>
                  <td className="text-white py-3 px-4">{student.attendance?.toFixed(1)}%</td>
                  <td className="text-white py-3 px-4">{student.grades?.toFixed(1)}</td>
                  <td className="text-white py-3 px-4">{student.risk_score?.toFixed(1)}%</td>
                  <td className="py-3 px-4">
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      student.risk_level === 'Alto' ? 'bg-red-500 text-white' :
                      student.risk_level === 'Médio' ? 'bg-amber-500 text-white' :
                      'bg-green-500 text-white'
                    }`}>
                      {student.risk_level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Footer */}
      <div className="mt-8 text-center text-purple-300 text-sm">
        <p className="font-semibold">EDUXO © 2025 - Plataforma Inteligente de Prevenção de Evasão Escolar</p>
        <p className="mt-1">Desenvolvido por Luís Felipe Lopes & Jonathas Villalba</p>
        <p className="mt-1">Projeto Integrador - Ciência de Dados | UNISO</p>
      </div>
    </div>
  );
};

export default EduxoDashboard;

