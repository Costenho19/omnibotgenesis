# OMNIX — Eureka Dubai Pitch Deck
## Version Final para Competencia | Febrero 2026

**Clasificacion**: Listo para Competencia
**Destino**: Eureka Dubai — Ronda Semifinal

---

## SLIDE 1 — TITULO

**OMNIX**
*Motor de Orquestacion de Capital e IA para Control de Riesgo*

> "La mejor operacion es, muchas veces, la que no se hace."

Harold Nunes — Fundador & Arquitecto de Producto
Pre-Seed | Febrero 2026

contacto@omnixquantum.net | www.omnixquantum.net

---

## SLIDE 2 — EL PROBLEMA (Gancho de 10 Segundos)

**El 95% de los sistemas de trading hacen la pregunta equivocada.**

Preguntan: *"Cuando deberia entrar al mercado?"*

La pregunta correcta es:

> **"Cuando NO deberia desplegarse capital?"**

**Lo que pasa hoy:**
- Los bots retail operan constantemente — incluso en condiciones peligrosas
- Sin deteccion de regimen = erosion de capital durante volatilidad
- Controles de riesgo de una sola capa que fallan bajo estres
- Narrativas de rendimiento enganosas y backtests sobreajustados
- $68B+ perdidos anualmente por traders retail a nivel global

**El resultado:** La destruccion de capital es la norma, no la excepcion.

La mayoria de los sistemas optimizan para *entradas*. Nadie optimiza para la *contencion*.

---

## SLIDE 3 — LA SOLUCION

**OMNIX es un motor de decision de IA risk-first que bloquea malas operaciones antes de que sucedan.**

A diferencia de los bots tradicionales que persiguen cada senal, OMNIX opera como un **sistema fail-closed**: si la confianza del edge cae por debajo de umbrales definidos, el despliegue de capital se detiene automaticamente.

**Tres Principios:**

| Principio | Que Significa |
|-----------|---------------|
| **Preservacion de Capital Primero** | Proteger antes de generar ganancia. Siempre. |
| **Arquitectura Fail-Closed** | El default = no operar. Debe ganarse el derecho a ejecutar. |
| **Auditabilidad Total** | Cada decision — ejecutada o bloqueada — queda registrada con justificacion completa. |

> "Saber cuando NO operar es un edge mas fuerte que forzar retornos."

---

## SLIDE 4 — COMO FUNCIONA (Arquitectura de Veto de 6 Capas)

**Cada senal debe sobrevivir 6 capas independientes antes de que el capital se mueva.**

```
Senal Detectada
    |
    v
+─────────────────────────+
|  Capa 1: MONTE CARLO    |  10,000 simulaciones de escenarios
|         VETO            |  Bloquea si Win Rate < 50% o Retorno Esperado < 0%
+────────────┬────────────+
             v
+─────────────────────────+
|  Capa 2: GESTION DE     |  Enforcement de riesgo a nivel portafolio
|     RIESGO VETO         |  Hard cap de drawdown maximo: 15%
+────────────┬────────────+
             v
+─────────────────────────+
|  Capa 3: PUERTA DE      |  Acuerdo de senales entre 5 modelos independientes
|       COHERENCIA        |  Bloquea si coherencia < 45%
+────────────┬────────────+
             v
+─────────────────────────+
|  Capa 4: VENTANA DE     |  Requiere 3 CICLOS CONSECUTIVOS de edge confirmado
|  CONFIRMACION DE EDGE   |  "Paciencia de capital" — sin entradas reactivas
+────────────┬────────────+
             v
+─────────────────────────+
|  Capa 5: DETECTOR DE    |  Deteccion de riesgo de cola en tiempo real
|      CISNE NEGRO        |  Reduccion automatica de exposicion durante estres
+────────────┬────────────+
             v
+─────────────────────────+
|  Capa 6: INDICE DE      |  Verificacion de contradiccion interna
|    CONTRADICCION        |  DCI >= 70 = HOLD obligatorio
+────────────┬────────────+
             v
       EJECUTAR o BLOQUEAR
```

**Resultado:** Solo las operaciones con edge multi-validado y persistente llegan a ejecucion.

La mayoria de los sistemas tienen 1 control de riesgo. OMNIX tiene 6 independientes que TODOS deben estar de acuerdo.

---

## SLIDE 5 — FOSO TECNOLOGICO (Por Que Esto Es Dificil de Copiar)

**Cinco capas de tecnologia defensible:**

| Tecnologia | Que Hace | Por Que Importa |
|------------|----------|-----------------|
| **Coherence Engine de 6 Niveles** | Fusiona 5 modelos de senales independientes con puntuacion ponderada | Ningun modelo individual puede anular el sistema |
| **Memoria Temporal No-Markoviana** | Detecta patrones de mercado mas alla de datos recientes usando memoria conductual autocorrelacionada | Ve lo que los modelos con sesgo de recencia no ven |
| **Edge Confirmation Window (ECW)** | Requiere persistencia del edge durante 3 ciclos consecutivos antes de ejecutar | Transforma "preservacion de capital" en "paciencia de capital" |
| **Motor de Shadow Portfolio** | Rastrea cada operacion vetada para aprender calibracion de filtros (192,000+ eventos capturados) | El sistema aprende de lo que NO hace |
| **Criptografia Post-Cuantica** | Ordenes firmadas con Dilithium-3 (alineado con NIST 2024 FIPS 204) | Seguridad a prueba de futuro — operacional hoy, no en roadmap |
| **Orquestacion Multi-Modelo de IA** | Gemini 2.5 Flash (primario) + GPT-4o + Claude Sonnet 4 con failover automatico | Sin dependencia de un solo proveedor de IA |

> "Cada decision queda registrada, trazable y revisable. Trail de auditoria completo."

---

## SLIDE 6 — TRACCION Y PRUEBA (Esto Es Real, No Teoria)

**OMNIX ha estado corriendo continuamente desde noviembre 2025 — en condiciones reales de mercado.**

### Linea de Tiempo de Validacion

```
CALIBRACION (COMPLETADA)         TRACK RECORD OFICIAL           REVISION DIA 30
Nov 2025 – Ene 14, 2026    →    Ene 15 – Feb 13, 2026    →    Feb 13, 2026
─────────────────────          ─────────────────────          ─────────────────
119 trades de prueba            28 dias completados            Evaluacion final
Motor de riesgo calibrado       Sistema corriendo 24/7         Decision Fase 2
Veto de 6 capas afinado         Capital preservado             Listo para inversores
```

### Metricas Clave

| Metrica | Valor | Fuente |
|---------|-------|--------|
| **Capital Preservado** | **98.5%** | PostgreSQL (verificado) |
| **Max Drawdown (observado)** | **1.5%** | Mientras BTC cayo 7.37% |
| **Ciclos de Evaluacion Analizados** | **192,000+** | Shadow Portfolio (PostgreSQL) |
| **Uptime del Sistema** | **95%+** | Logs de produccion Railway |
| **Latencia de Ejecucion** | **~120ms** | Medido, no estimado |
| **Cobertura de Telemetria** | **100%** | Cada decision registrada |
| **Dia del Track Record** | **28 de 30** | Periodo oficial |

### La Prueba de Concepto

Durante el periodo del track record, el Detector de Cisne Negro de OMNIX identifico 50%+ de probabilidad de crash en multiples activos. La respuesta del sistema: **detencion automatica de trading. Cero exposicion durante la volatilidad.**

> **Esto es el producto FUNCIONANDO — no el producto fallando.**
> La decision de NO operar ES la propuesta de valor.

---

## SLIDE 7 — PANORAMA COMPETITIVO

**La mayoria de los competidores optimizan para entradas. OMNIX optimiza para la contencion.**

| Caracteristica | Bots Retail | Fondos Quant | OMNIX |
|----------------|:-----------:|:------------:|:-----:|
| Arquitectura Risk-First | No | Parcial | **Si** |
| Sistema Fail-Closed | No | No | **Si** |
| Veto Multi-Capa (6 independientes) | No | 1-2 capas | **6 capas** |
| Deteccion de Regimen en Tiempo Real | No | Si | **Si** |
| Seguridad Post-Cuantica (Produccion) | No | No | **Si** |
| Auditabilidad Total de Decisiones | No | Solo interna | **Si** |
| Aprendizaje Shadow Portfolio | No | No | **Si** |
| Enfoque en Preservacion de Capital | No | Parcial | **Si** |
| Accesible a Capital Externo | Si | No | **Si** |

**La brecha que llenamos:**
- Las herramientas retail carecen de controles de riesgo institucionales
- Las herramientas institucionales estan bloqueadas detras de minimos de $10M+
- OMNIX conecta ambos mundos: rigor institucional, infraestructura accesible

---

## SLIDE 8 — MODELO DE NEGOCIO (Motor de Ingreso Dual)

### Flujo 1: B2C SaaS — Usuarios Directos

| Nivel | Precio | Caracteristicas |
|-------|--------|-----------------|
| **Starter** | $49/mes | Monitoreo de riesgo basico, alertas de regimen |
| **Pro** | $149/mes | Acceso completo a Risk Guardian, trail de auditoria |
| **Advanced** | $499/mes | Acceso API, configuracion de veto personalizada, soporte prioritario |

### Flujo 2: B2B Enterprise Licensing — Plataformas e Instituciones

| Producto | Precio | Comprador |
|----------|--------|-----------|
| **Risk Guardian API** | $10K–50K/mes | Plataformas de trading (3Commas, NinjaTrader) |
| **Motor White-Label** | $100K+ setup + $20K/mes | Brokers, exchanges, prop firms |
| **Per-Validacion** | $0.01–0.05/llamada | Pago por uso |

**Caso de Uso Enterprise:**

```
Trader de prop firm envia orden → OMNIX Risk Gate valida en <100ms →
APROBAR (con trail de auditoria) o VETAR (con justificacion completa)

Impacto: -40% eventos de drawdown, 100% compliance de auditoria, cero costo de desarrollo para la firma.
```

### Proyecciones de Ingreso (Conservadoras)

| Ano | Modelo | Ingreso |
|-----|--------|---------|
| Ano 1 | SaaS temprano + 1 piloto Enterprise | $200K–400K |
| Ano 2 | Crecimiento SaaS + 3-5 licencias Enterprise | $800K–1.2M |
| Ano 3 | Escala + expansion geografica | $2M+ |

> "Las instituciones pagan por lo que BLOQUEA malas operaciones, no por alpha."
> Ingreso basado en licencias. Sin tokens. Sin fees de rendimiento sobre capital de usuarios.

---

## SLIDE 9 — OPORTUNIDAD DE MERCADO

### Los Numeros

| Mercado | Tamano |
|---------|--------|
| Volumen diario global de trading crypto | **$2.3T+** |
| Mercado de trading algoritmico | **$18.8B** (creciendo 12% CAGR) |
| Usuarios avanzados de crypto globalmente | **21M** |
| Mercado direccionable accesible | **2.1M usuarios** (segmento avanzado 10%) |
| Objetivo inicial | **10,500 usuarios** (0.5% penetracion) |

### La Brecha

La gestion de riesgo institucional existe — pero esta encerrada dentro de hedge funds con $100M+ AUM. NO hay infraestructura accesible para:

- Family offices entrando a crypto
- Fondos regulados (ADGM, DIFC, Dubai)
- Prop trading firms
- Individuos de alto patrimonio gestionando su propio capital
- Plataformas de trading que quieren agregar gobernanza de riesgo

### Por Que Ahora

Dos fuerzas convergiendo:

1. **Capital institucional esta entrando a crypto** — pero sin infraestructura de riesgo adecuada
2. **La regulacion se esta endureciendo** — ADGM, MiCA, SEC todos requiriendo auditabilidad y controles de riesgo

El mercado necesita infraestructura de riesgo. No mas senales de trading.

---

## SLIDE 10 — POR QUE DUBAI Y MENA

**Alineacion estrategica con la vision de la region:**

| Factor | Por Que Importa |
|--------|-----------------|
| **ADGM** | Marco regulatorio de clase mundial para activos digitales |
| **Capital soberano** | Desplegando activamente en fintech e IA |
| **Hub71 / DIFC** | Acceso directo a red de inversores institucionales |
| **Regulacion pro-crypto** | Claridad que los mercados occidentales aun no tienen |
| **Posicion geografica** | Puente entre Asia, Europa y Africa |
| **Sofisticacion de inversores** | Asignadores de capital que valoran disciplina sobre hype |

**OMNIX esta construido para entornos regulados.** La transicion del "salvaje oeste crypto" a infraestructura institucional esta sucediendo aqui primero.

---

## SLIDE 11 — FUNDADOR Y EQUIPO

**Harold Nunes**
*Fundador & Arquitecto de Producto*

- Construyo OMNIX desde concepto hasta sistema corriendo en produccion
- Diseno la arquitectura de veto de 6 capas, motor de riesgo y orquestacion de IA
- Tecnologo autodidacta con disciplina de finanzas institucionales
- Reubicandose a Dubai para ecosistema ADGM/Hub71

**Estructura Actual:**
- Arquitectura core, logica de riesgo y roadmap: Liderado por el fundador
- Implementacion e ingenieria: Desarrolladores externos de confianza
- Advisory: Construyendo red en ecosistema ADGM/Hub71

**Que Hace Efectivo a Este Equipo:**
- Velocidad de ejecucion sobre tamano del equipo
- Validacion en mercado real desde el dia uno
- Producto ya corriendo en produccion 24/7
- La ronda de $500K incluye expansion del equipo de ingenieria

**LinkedIn:** linkedin.com/in/harold-nunes-21bb65285

---

## SLIDE 12 — EL ASK

### Ronda Pre-Seed

| Item | Detalles |
|------|----------|
| **Levantando** | **$500,000 USD** |
| **Equity** | **10%** |
| **Valoracion Pre-Money** | **$4.5M–$5M** |

### Uso de Fondos

| Categoria | Asignacion | Proposito |
|-----------|:----------:|-----------|
| Estrategia y Motor de Riesgo | 35% | Refinar algoritmos de decision, expandir aprendizaje del Shadow Portfolio |
| Legal y Regulatorio Dubai/ADGM | 25% | Formacion de empresa, estructura regulatoria |
| Infraestructura Institucional | 20% | API Enterprise, dashboard, certificaciones de seguridad |
| Equipo y Operaciones | 15% | 2-3 contrataciones clave de ingenieria |
| Reserva | 5% | Contingencia |

### Hitos con Financiacion

| Tiempo | Hito |
|--------|------|
| Mes 1 | Completar track record de 30 dias, iniciar outreach institucional |
| Mes 3 | Primer piloto enterprise (prop firm o plataforma de trading) |
| Mes 6 | Estructura regulatoria ADGM completa |
| Mes 9 | Primeros $1M en volumen de riesgo gestionado por plataforma |
| Mes 12 | Preparacion para Series A con metricas validadas |

> "El enfoque de preservacion de capital se extiende a TU capital tambien."

---

## SLIDE 12B — POR QUE OMNIX GANA (Cierre)

### El Caso en 60 Segundos

1. **El problema es masivo** — $68B+ perdidos por traders retail anualmente, cero infraestructura de riesgo accesible
2. **El timing es perfecto** — Las instituciones entrando a crypto necesitan gobernanza de riesgo AHORA
3. **El producto existe** — No es un slide deck. Corriendo en produccion por 3+ meses.
4. **El enfoque es unico** — Nadie mas optimiza para la contencion
5. **La data es real** — 192,000+ eventos, 98.5% capital preservado, trail de auditoria completo
6. **El mercado esta aqui** — Dubai/ADGM es el epicentro de infraestructura crypto institucional

> "La mayoria de los sistemas de trading preguntan: 'Como gano dinero?'
> OMNIX pregunta: 'Como me aseguro de no perderlo?'
> Esa pregunta vale $500K para responderla a escala."

---

## APENDICE A — DECISION TRACE (Output del Sistema en Vivo)

```json
{
  "timestamp": "2026-02-10T14:23:45Z",
  "symbol": "BTC/USD",
  "decision": "BLOCKED",
  "layers": {
    "monte_carlo": {
      "win_rate": "48.7%",
      "expected_return": "-0.22%",
      "verdict": "VETO"
    },
    "risk_management": {
      "portfolio_exposure": "0%",
      "drawdown_status": "WITHIN_LIMITS",
      "verdict": "PASS"
    },
    "coherence_gate": {
      "score": "44%",
      "threshold": "45%",
      "verdict": "VETO"
    },
    "ecw": {
      "cycles": "0/3",
      "status": "WAITING",
      "verdict": "VETO"
    },
    "black_swan": {
      "severity": "LOW",
      "crash_probability": "12%",
      "verdict": "PASS"
    },
    "dci": {
      "contradiction_index": 62,
      "threshold": 70,
      "verdict": "PASS"
    }
  },
  "final_decision": "BLOCKED — 3 de 6 capas vetaron",
  "capital_preserved": "$47,500 (tamano de posicion evitado)"
}
```

> Cada decision que OMNIX toma se ve asi. Completamente trazable. Completamente auditable. Nada oculto.

---

## APENDICE B — DOCUMENTOS CLAVE PARA DUE DILIGENCE

| Documento | Descripcion |
|-----------|-------------|
| Executive Fact Sheet | Estado del sistema y marco de gobernanza |
| Track Record Case Study | Narrativa dia a dia de proteccion de capital |
| Product Overview | Posicionamiento completo del producto |
| Risk Guardian Technical Spec | Detalles de arquitectura del sistema de veto de 6 niveles |
| Shadow Portfolio Report | Analisis contrafactual de 192,000+ operaciones |
| Architecture Decision Records | 22+ decisiones tecnicas documentadas (ADRs) |
| System State Manifest | Configuracion en vivo (JSON, legible por maquina) |

**Todos los documentos disponibles bajo solicitud para inversores calificados.**

---

## CONTACTO

**Harold Nunes** — Fundador & Arquitecto de Producto

| Canal | Contacto |
|-------|----------|
| Email | contacto@omnixquantum.net |
| Telefono | +1 (650) 507-8293 |
| WhatsApp | +1 (650) 481-5494 |
| Website | www.omnixquantum.net |
| LinkedIn | linkedin.com/in/harold-nunes-21bb65285 |

---

*OMNIX — Protegiendo Capital Primero*
*Eureka Dubai 2026 — Semifinalista*

---

**Disclaimer:** Este documento describe actividad de paper trading durante un periodo de validacion. Todas las metricas son de trading simulado en condiciones reales de mercado. El rendimiento pasado, simulado o real, no garantiza resultados futuros. OMNIX no es un producto de inversion y no ofrece retornos garantizados. Las proyecciones de ingresos son estimaciones basadas en supuestos conservadores.
