# 🧠 COMMUNITY INTELLIGENCE SYSTEM - Documentación Técnica

## Fecha: 25 de Noviembre, 2025
## Versión: V6.0 ULTRA
## Feature: Sistema de Memoria Colectiva / Inteligencia Comunitaria

---

## 📋 RESUMEN EJECUTIVO

El Sistema de Inteligencia Colectiva permite que OMNIX aprenda de TODOS sus usuarios. 
Cada vez que un usuario reporta si una señal funcionó o falló, esa información se almacena
y analiza para mejorar las estrategias ARES.

**IMPORTANTE:** Este sistema NO modifica ARES automáticamente. Solo recopila datos y
genera sugerencias que Harold debe aprobar manualmente.

---

## 🏗️ ARQUITECTURA DEL SISTEMA

```
omnix_services/community_intelligence/
├── __init__.py                 # Exports principales
├── feedback_manager.py         # Gestión de feedback (449 líneas)
├── community_analyzer.py       # Análisis con AI (345 líneas)
├── reward_system.py            # Sistema de puntos/badges (274 líneas)
└── community_dashboard.py      # Dashboard estadísticas (320 líneas)
```

**Total: ~1,388 líneas de código nuevo**

---

## 📊 ESQUEMA DE BASE DE DATOS

### Tabla: `community_feedback`
```sql
CREATE TABLE community_feedback (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT,
    feedback_type TEXT NOT NULL,        -- 'signal', 'strategy', 'arbitrage'
    signal_type TEXT,                    -- 'BUY', 'SELL', NULL
    strategy TEXT,                       -- 'ARES_V1', 'ARES_V2', etc.
    symbol TEXT,                         -- 'BTC/USD', etc.
    result TEXT NOT NULL,                -- 'success', 'failure', 'partial'
    market_condition TEXT,               -- 'bullish', 'bearish', 'sideways'
    btc_price REAL,
    volatility TEXT,                     -- 'low', 'medium', 'high'
    timeframe TEXT,                      -- '1m', '5m', '1h', etc.
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT false,
    helpful_votes INTEGER DEFAULT 0
);
```

### Tabla: `strategy_votes`
```sql
CREATE TABLE strategy_votes (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    strategy TEXT NOT NULL,
    vote INTEGER NOT NULL,               -- 1-5 estrellas
    reason TEXT,
    market_condition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, strategy, DATE(created_at))  -- 1 voto por día por estrategia
);
```

### Tabla: `improvement_proposals`
```sql
CREATE TABLE improvement_proposals (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT,
    proposal_type TEXT NOT NULL,         -- 'feature', 'bug', 'improvement', 'strategy'
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_strategy TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending',       -- 'pending', 'approved', 'rejected', 'implemented'
    ai_analysis TEXT,
    community_votes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    implemented_at TIMESTAMP
);
```

### Tabla: `user_contributions`
```sql
CREATE TABLE user_contributions (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    total_feedback INTEGER DEFAULT 0,
    helpful_feedback INTEGER DEFAULT 0,
    total_votes INTEGER DEFAULT 0,
    proposals_submitted INTEGER DEFAULT 0,
    proposals_accepted INTEGER DEFAULT 0,
    contribution_points INTEGER DEFAULT 0,
    contribution_level TEXT DEFAULT 'Novato',
    badges TEXT DEFAULT '[]',            -- JSON array de badges
    first_contribution TIMESTAMP,
    last_contribution TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla: `detected_patterns`
```sql
CREATE TABLE detected_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type TEXT NOT NULL,          -- 'high_failure', 'market_specific', etc.
    description TEXT NOT NULL,
    affected_strategy TEXT,
    market_condition TEXT,
    confidence REAL NOT NULL,            -- 0.0 - 1.0
    sample_size INTEGER NOT NULL,
    success_rate REAL,
    failure_rate REAL,
    suggestion TEXT,
    status TEXT DEFAULT 'detected',      -- 'detected', 'approved', 'rejected', 'implemented'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    implemented_at TIMESTAMP
);
```

---

## 📱 COMANDOS TELEGRAM IMPLEMENTADOS

### `/feedback [estrategia] [resultado] [comentario]`
Reportar si una señal funcionó o no.

**Parámetros:**
- `estrategia`: ARES_V1, ARES_V2, ARBITRAGE
- `resultado`: success, failure, partial
- `comentario`: (opcional) texto adicional

**Ejemplo:**
```
/feedback ARES_V1 success Excelente señal en mercado bullish
/feedback ARES_V2 failure Falló en mercado lateral
```

**Puntos:** +10 por cada feedback

---

### `/vote_strategy [estrategia] [1-5] [razón]`
Votar por una estrategia con estrellas.

**Parámetros:**
- `estrategia`: ARES_V1, ARES_V2, ARBITRAGE
- `voto`: 1 (malo) a 5 (excelente)
- `razón`: (opcional)

**Ejemplo:**
```
/vote_strategy ARES_V1 5 Excelente rendimiento constante
```

**Puntos:** +5 por cada voto

---

### `/community_stats`
Ver estadísticas globales de la comunidad.

**Muestra:**
- Total de contribuidores
- Feedback total y success rate
- Rating promedio de estrategias
- Propuestas pendientes
- Patrones detectados por AI

---

### `/top_strategies`
Ranking de estrategias según la comunidad.

**Muestra:**
- Top 3 estrategias con medallas
- Rating promedio, votos totales
- Success rate según feedback
- Health status (Excelente/Bueno/Regular/Bajo)

---

### `/my_contributions`
Ver tu perfil de contribuidor.

**Muestra:**
- Nivel actual y puntos
- Rank en el leaderboard
- Estadísticas de feedback
- Badges ganados
- Progreso al siguiente nivel

---

### `/leaderboard`
Top 10 contribuidores de la comunidad.

---

### `/analyze_patterns` (Solo Admin)
Ejecutar análisis AI de patrones en feedback.

**Proceso:**
1. Analiza últimos 30 días de feedback
2. Detecta patrones de fallos recurrentes
3. Genera sugerencias con Gemini AI
4. Guarda patrones para revisión de Harold

---

## 🏆 SISTEMA DE RECOMPENSAS

### Puntos por Acción:
| Acción | Puntos |
|--------|--------|
| Feedback | +10 |
| Voto estrategia | +5 |
| Propuesta mejora | +25 |
| Feedback marcado útil | +15 bonus |

### Niveles de Contribuidor:
| Nivel | Emoji | Puntos Mínimos |
|-------|-------|----------------|
| Nuevo | 🌱 | 0 |
| Novato | 🌿 | 10 |
| Aprendiz | 🌳 | 50 |
| Intermedio | ⭐ | 100 |
| Avanzado | 🌟 | 300 |
| Experto | 💫 | 500 |
| Maestro | 🏆 | 1000 |
| Leyenda | 👑 | 2500 |

### Badges Disponibles:
- 🎯 Primer Feedback
- 📊 Entusiasta (10+ feedbacks)
- 🎖️ Maestro del Feedback (50+ feedbacks)
- 💎 Contribuidor Valioso (5+ feedbacks útiles)
- 💡 Generador de Ideas (1+ propuestas)
- 🚀 Innovador (propuesta implementada)
- ⭐ Estrella Emergente (100+ puntos)
- 👑 Líder Comunitario (500+ puntos)
- 🏆 Leyenda OMNIX (1000+ puntos)

---

## 🔍 ANÁLISIS AI DE PATRONES

### Proceso:
1. **Recolección**: Agrupa feedback por estrategia + condición de mercado
2. **Análisis**: Identifica combinaciones con alto failure rate (>40%)
3. **AI Processing**: Gemini analiza patrones y genera insights
4. **Detección**: Guarda patrones problemáticos en `detected_patterns`
5. **Revisión**: Harold aprueba/rechaza patrones detectados

### Output de Análisis:
```python
{
    'patterns_analyzed': 15,
    'patterns_detected': 3,
    'patterns': [
        {
            'pattern_type': 'high_failure',
            'description': 'Alta tasa de fallos (65%) para ARES_V2 en mercado sideways',
            'affected_strategy': 'ARES_V2',
            'market_condition': 'sideways',
            'confidence': 0.85,
            'sample_size': 20,
            'suggestion': 'Revisar ARES_V2 en condiciones de mercado sideways'
        }
    ],
    'ai_analysis': 'Análisis detallado de Gemini...'
}
```

---

## 🔧 INTEGRACIÓN CON BOT

### En enterprise_bot.py:

**Imports agregados (líneas 47-58):**
```python
from omnix_services.community_intelligence import (
    CommunityFeedbackManager,
    CommunityAnalyzer,
    RewardSystem,
    CommunityDashboard
)
```

**Inicialización (líneas 240-262):**
```python
if COMMUNITY_INTELLIGENCE_AVAILABLE:
    self.feedback_manager = CommunityFeedbackManager()
    self.community_analyzer = CommunityAnalyzer()
    self.reward_system = RewardSystem()
    self.community_dashboard = CommunityDashboard()
```

**Command Handlers (líneas 346-355):**
```python
self.application.add_handler(CommandHandler("feedback", self.feedback_command))
self.application.add_handler(CommandHandler("community_stats", self.community_stats_command))
self.application.add_handler(CommandHandler("top_strategies", self.top_strategies_command))
self.application.add_handler(CommandHandler("my_contributions", self.my_contributions_command))
self.application.add_handler(CommandHandler("vote_strategy", self.vote_strategy_command))
self.application.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
self.application.add_handler(CommandHandler("analyze_patterns", self.analyze_patterns_command))
```

---

## 🧪 TESTING PROCEDURES

### Test 1: Feedback básico
```
1. Enviar: /feedback ARES_V1 success
2. Verificar: Respuesta con puntos ganados (+10)
3. Verificar: /my_contributions muestra feedback registrado
```

### Test 2: Votación de estrategia
```
1. Enviar: /vote_strategy ARES_V1 5
2. Verificar: Respuesta con estrellas y puntos (+5)
3. Verificar: /top_strategies muestra el voto
```

### Test 3: Dashboard comunitario
```
1. Enviar: /community_stats
2. Verificar: Muestra estadísticas globales
3. Verificar: Datos actualizados después de feedback
```

### Test 4: Leaderboard
```
1. Enviar: /leaderboard
2. Verificar: Lista de top 10 contribuidores
3. Verificar: Tu posición y puntos
```

### Test 5: Análisis de patrones (Admin)
```
1. Generar varios feedbacks con resultado 'failure'
2. Enviar: /analyze_patterns
3. Verificar: Detecta patrones problemáticos
4. Verificar: AI analysis incluido (si hay suficientes datos)
```

---

## ⚠️ NOTAS IMPORTANTES

1. **NO MODIFICA ARES AUTOMÁTICAMENTE**
   - El sistema solo recopila datos y genera sugerencias
   - Harold debe aprobar cualquier cambio manualmente

2. **PRIVACY**
   - Se almacenan user_id y username para tracking
   - Feedback es visible en estadísticas agregadas

3. **RATE LIMITING**
   - Un voto por día por estrategia por usuario
   - Sin límite en feedback (incentiva más datos)

4. **AI ANALYSIS**
   - Requiere GEMINI_API_KEY configurado
   - Funciona sin AI (solo análisis estadístico)

---

## 📞 CONTACTO

Para preguntas sobre esta implementación:
- **Desarrollador:** Replit Agent
- **Fecha:** 25 de Noviembre, 2025
- **Proyecto:** OMNIX V6.0 ULTRA
