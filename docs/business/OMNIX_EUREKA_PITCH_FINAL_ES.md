# OMNIX — Eureka Dubai Pitch Deck
## Version Final para Competencia | Febrero 2026

**Clasificacion**: Listo para Competencia — Revisado por Expertos
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
- $68B+ perdidos anualmente por traders retail a nivel global

**El resultado:** La destruccion de capital es la norma, no la excepcion.

La mayoria de los sistemas optimizan para *entradas*. Nadie optimiza para la *contencion*.

---

## SLIDE 3 — LA SOLUCION

**OMNIX es un motor de decision de IA risk-first que bloquea malas operaciones antes de que sucedan.**

A diferencia de los bots de trading que persiguen cada senal, OMNIX opera como un **sistema fail-closed**: si la confianza del edge cae por debajo de umbrales definidos, el despliegue de capital se detiene automaticamente.

**Tres Principios:**

| Principio | Que Significa |
|-----------|---------------|
| **Preservacion de Capital Primero** | Proteger antes de generar ganancia. Siempre. |
| **Arquitectura Fail-Closed** | El default = no operar. Debe ganarse el derecho a ejecutar. |
| **Auditabilidad Total** | Cada decision — ejecutada o bloqueada — queda registrada con justificacion completa. |

> "Saber cuando NO operar es un edge mas fuerte que forzar retornos."

---

## SLIDE 4 — COMO FUNCIONA (6 Checkpoints de Seguridad)

**Piensa en esto como seguridad de aeropuerto para tu capital.**

Cada senal de trading debe pasar por 6 checkpoints de seguridad independientes. Si CUALQUIERA falla, la operacion se bloquea automaticamente.

```
Senal de Trading Llega
        |
        v
  +─────────────────────────────────────────────+
  | 1. CHECK DE PROBABILIDAD                     |
  |    "Es probable que este trade gane?"         |
  |    Corre 10,000 escenarios simulados          |
  |    Bloquea si probabilidad de ganar < 50%     |
  +──────────────────────┬──────────────────────+
                         v
  +─────────────────────────────────────────────+
  | 2. LIMITE DE RIESGO                          |
  |    "Esto excederia limites seguros?"          |
  |    Enforcement de drawdown maximo: 15%        |
  +──────────────────────┬──────────────────────+
                         v
  +─────────────────────────────────────────────+
  | 3. ACUERDO DE SENALES                        |
  |    "5 modelos independientes estan de acuerdo?"|
  |    Requiere 45%+ de consenso entre modelos    |
  +──────────────────────┬──────────────────────+
                         v
  +─────────────────────────────────────────────+
  | 4. CONFIRMACION DE TENDENCIA                 |
  |    "Es sostenido — o solo ruido?"             |
  |    Requiere edge por 3 ciclos consecutivos    |
  +──────────────────────┬──────────────────────+
                         v
  +─────────────────────────────────────────────+
  | 5. PRUEBA DE ESTRES                          |
  |    "Que pasa si el mercado se desploma ahora?"|
  |    Deteccion de riesgo de cola en tiempo real  |
  +──────────────────────┬──────────────────────+
                         v
  +─────────────────────────────────────────────+
  | 6. CHECK LOGICO                              |
  |    "Las senales se contradicen entre si?"     |
  |    Alta contradiccion = hold obligatorio      |
  +──────────────────────┬──────────────────────+
                         v
                APROBADO o BLOQUEADO
```

**LOS 6 deben aprobar — o la operacion se bloquea.**

La mayoria de los sistemas tienen 1 control de riesgo. OMNIX tiene 6 independientes que TODOS deben estar de acuerdo.

> "La seguridad del aeropuerto no te deja pasar si un scanner falla. OMNIX tampoco."

---

## SLIDE 5 — LA OPERACION QUE NO SUCEDIO

**Esto es nuestro producto FUNCIONANDO — no fallando.**

### Escenario Real: 3 de Febrero, 2026 — Breakout de BTC

```
Condiciones del Mercado:
  Accion de Precio BTC:   +6% en 2 horas
  Sentimiento:            Euforico
  Bot Tradicional:        Ejecutaria posicion de $50,000

Decision de OMNIX:
┌──────────────────────────────────────────────┐
│ Checkpoint 1: Probabilidad    → PASA    ✓   │
│ Checkpoint 2: Limites Riesgo  → PASA    ✓   │
│ Checkpoint 3: Acuerdo Senales → PASA    ✓   │
│ Checkpoint 4: Conf. Tendencia → FALLA   ✗   │
│ Checkpoint 5: Prueba Estres   → ALERTA  ⚠   │
│ Checkpoint 6: Check Logico    → PASA    ✓   │
│                                              │
│ DECISION: ██ BLOQUEADO ██                    │
│ Razon: Persistencia de tendencia insuficiente│
│        (spike de momentum, no edge sostenido)│
└──────────────────────────────────────────────┘

48 Horas Despues:
  BTC cayo -9%
  Perdida del bot tradicional: -$4,500
  Exposicion de OMNIX: $0

Capital Preservado: $50,000
```

**Esto es lo que "fail-closed" significa en la practica.** El sistema identifico que el breakout carecia de persistencia — una trampa clasica que destruye capital.

> "Un bot tradicional habria comprado en la euforia. OMNIX espero — y tenia razon."

---

## SLIDE 6 — TRACCION Y PRUEBA (Esto Es Real, No Teoria)

**OMNIX ha estado corriendo continuamente desde noviembre 2025 — en condiciones reales de mercado.**

### Performance del Track Record

```
 FASE DE CALIBRACION             TRACK RECORD OFICIAL           SIGUIENTE FASE
 Nov 2025 – Ene 14, 2026   →    Ene 15 – Feb 13, 2026    →    Fase 2
 119 trades de prueba            30 dias completados            Optimizacion
 Motor de riesgo calibrado       Capital preservado             gradual de
 Veto de 6 capas afinado         Sistema corriendo 24/7         rentabilidad
```

### Metricas Clave

| Metrica | Valor | Contexto |
|---------|-------|----------|
| **Capital Preservado** | **98.5%** | Durante periodo donde BTC cayo 7.37% |
| **Max Drawdown** | **1.5%** | vs drawdown maximo de BTC de -7.37% |
| **Trades Bloqueados** | **47** | Senales de alto riesgo correctamente vetadas |
| **Tasa de Exito de Bloqueos** | **91%** | Trades bloqueados habrian perdido dinero |
| **Ciclos de Decision Analizados** | **192,000+** | Motor de aprendizaje Shadow Portfolio |
| **Uptime del Sistema** | **95%+** | Produccion (Railway), no ambiente de prueba |
| **Latencia de Ejecucion** | **~120ms** | Medido, no estimado |

### Que Significan Estos Numeros

Mientras Bitcoin cayo 7.37%, OMNIX preservo 98.5% del capital. De las 47 operaciones que bloqueo, el 91% habrian resultado en perdidas.

**La contencion del sistema salvo capital — esa ES la propuesta de valor.**

> "No medimos el exito por cuanto ganamos. Lo medimos por cuanto no perdimos."

---

## SLIDE 7 — FOSO TECNOLOGICO (Por Que Esto Es Dificil de Copiar)

**Seis capas de tecnologia defensible construidas en 3+ meses de operacion en mercado real:**

| Tecnologia | Explicacion Simple | Ventaja Competitiva |
|------------|-------------------|---------------------|
| **Motor de Seguridad de 6 Checkpoints** | 5 modelos de IA independientes deben coincidir antes de cualquier operacion | Ningun modelo individual puede anular el sistema |
| **Sistema de Memoria Conductual** | Recuerda patrones del mercado mas alla de datos recientes | Ve lo que otros sistemas no ven |
| **Ventana de Confirmacion de Edge** | Requiere persistencia de tendencia por 3 ciclos — no solo un spike | Transforma "preservacion" en "paciencia" |
| **Motor Shadow Portfolio** | Rastrea cada operacion vetada para aprender (192,000+ eventos) | El sistema aprende de lo que NO hace |
| **Seguridad Post-Cuantica** | Ordenes firmadas con Dilithium-3 (NIST FIPS 204) | Operacional hoy — no en roadmap |
| **Orquestacion Multi-IA** | Gemini 2.5 Flash + GPT-4o + Claude Sonnet 4 con failover | Cero dependencia de un solo proveedor |

> "Cada decision queda registrada, trazable y revisable. Trail de auditoria — siempre."

---

## SLIDE 8 — MODELO DE NEGOCIO (Infraestructura de Riesgo B2B)

### PRIMARIO: Infraestructura de Riesgo B2B — Licenciamiento a Instituciones

| Tipo de Cliente | Caso de Uso | Precio |
|-----------------|-------------|--------|
| **Prop Trading Firms** (200+ en ADGM/DIFC) | Proteger capital de traders con puertas de riesgo automatizadas | $15K–50K/mes |
| **Plataformas de Trading** (3Commas, NinjaTrader) | Risk-as-a-Service para sus usuarios | $0.01–0.05/validacion |
| **Fondos Regulados** (compliance MiCA) | Trail de auditoria + gobernanza de riesgo para compliance | $100K+ licencia anual |

**Como Funciona para un Prop Firm:**

```
Trader envia orden
    → OMNIX Risk Gate valida en <100ms
    → APROBAR (con trail de auditoria) o BLOQUEAR (con justificacion completa)

Impacto para la firma:
  -40% eventos de drawdown
  100% compliance de auditoria
  Cero costo de desarrollo (licencian, no construyen)
```

### SECUNDARIO: B2C SaaS — Traders Individuales (Post-Validacion Enterprise)

| Nivel | Precio | Caracteristicas |
|-------|--------|-----------------|
| **Pro** | $149/mes | Risk Guardian completo, trail de auditoria de decisiones |
| **Advanced** | $499/mes | Acceso API, configuracion de veto personalizada |

### Proyecciones de Ingreso (Conservadoras)

| Ano | Enfoque | Ingreso |
|-----|---------|---------|
| Ano 1 | 3 pilotos enterprise + SaaS temprano | $200K–400K |
| Ano 2 | 5-8 licencias enterprise + crecimiento SaaS | $800K–1.2M |
| Ano 3 | Escala + expansion geografica (ADGM → EU MiCA) | $2M+ |

> "Las instituciones pagan por lo que BLOQUEA malas operaciones, no por alpha."
> Ingreso basado en licencias. Sin tokens. Sin fees de rendimiento.

---

## SLIDE 9 — OPORTUNIDAD DE MERCADO

### Los Numeros

| Mercado | Tamano |
|---------|--------|
| Volumen diario global de trading crypto | **$2.3T+** |
| Mercado de trading algoritmico | **$18.8B** (creciendo 12% CAGR) |
| Prop firms solo en ADGM/DIFC | **200+** |
| Plataformas que necesitan compliance MiCA (2025+) | **2,000+** |
| Objetivo Ano 1 | **3 pilotos enterprise** |

### La Brecha Que Nadie Esta Llenando

La gestion de riesgo institucional existe — dentro de hedge funds con $100M+ AUM. NO hay infraestructura de riesgo accesible para:

- Prop trading firms que necesitan proteger capital de traders
- Plataformas de trading agregando gobernanza de riesgo para compliance
- Fondos regulados (ADGM, DIFC, MiCA) que necesitan trails de auditoria
- Family offices entrando a crypto sin herramientas institucionales

### Por Que Ahora — Dos Fuerzas Convergiendo

1. **Capital institucional esta inundando crypto** — pero sin infraestructura de riesgo adecuada
2. **Regulacion MiCA (EU) + requisitos ADGM** — las plataformas DEBEN tener controles de riesgo y trails de auditoria

> El mercado necesita infraestructura de riesgo. No mas senales de trading.
> El reloj regulatorio esta corriendo — y OMNIX esta listo.

---

## SLIDE 10 — POR QUE DUBAI Y MENA

**Alineacion estrategica con la vision de la region:**

| Factor | Por Que Importa |
|--------|-----------------|
| **ADGM** | Marco regulatorio de clase mundial para activos digitales |
| **Capital soberano** | Desplegando activamente en fintech e IA |
| **Hub71 / DIFC** | Acceso directo a red de inversores institucionales |
| **200+ prop firms** | Mercado direccionable inmediato en la region |
| **Posicion geografica** | Puente entre Asia, Europa y Africa |
| **Sofisticacion de inversores** | Asignadores de capital que valoran disciplina sobre hype |

**OMNIX esta construido para entornos regulados.** La transicion del "salvaje oeste crypto" a infraestructura institucional esta sucediendo aqui primero.

---

## SLIDE 11 — FUNDADOR Y EQUIPO

**Harold Nunes**
*Fundador & Arquitecto de Producto*

- Construyo OMNIX desde concepto hasta sistema corriendo en produccion — solo
- Diseno el motor de seguridad de 6 checkpoints, logica de riesgo y orquestacion de IA
- Tecnologo autodidacta con disciplina de finanzas institucionales
- Reubicandose a Dubai para ecosistema ADGM/Hub71

**Estructura Actual:**
- Arquitectura core, logica de riesgo y roadmap: Liderado por el fundador
- Implementacion e ingenieria: Desarrolladores externos de confianza
- Advisory: Construyendo red en ecosistema ADGM/Hub71

**Por Que Funciona:**
- Velocidad de ejecucion sobre tamano del equipo — producto ya corriendo 24/7
- Validacion en mercado real desde el dia uno — no investigacion teorica
- La ronda de $500K incluye 2-3 contrataciones clave de ingenieria para API enterprise

**LinkedIn:** linkedin.com/in/harold-nunes-21bb65285

---

## SLIDE 12 — EL ASK

### Ronda Pre-Seed

| Item | Detalles |
|------|----------|
| **Levantando** | **$500,000 USD** |
| **Equity** | **16.7%** |
| **Valoracion Pre-Money** | **$2.5M–$3M** |

### Justificacion de Valoracion

| Factor | Evidencia |
|--------|-----------|
| Producto funcionando en produccion | 3+ meses corriendo 24/7 |
| Data de validacion real | 192,000+ ciclos de decision analizados |
| IP defensible | Arquitectura de 6 checkpoints + Motor Shadow Portfolio |
| Timing estrategico | Convergencia MiCA + ADGM creando demanda urgente |
| Comparable | Chainalysis levanto a $4M pre-money en etapa similar |

### Uso de Fondos

| Categoria | Asignacion | Proposito |
|-----------|:----------:|-----------|
| Estrategia y Motor de Riesgo | 35% | Refinar algoritmos, expandir aprendizaje Shadow Portfolio |
| Legal y Regulatorio Dubai/ADGM | 25% | Formacion de empresa, estructura regulatoria |
| Infraestructura Enterprise | 20% | API para prop firms, certificaciones de seguridad |
| Equipo y Operaciones | 15% | 2-3 contrataciones clave de ingenieria |
| Reserva | 5% | Contingencia |

### Hitos con Financiacion

| Tiempo | Hito |
|--------|------|
| Mes 1 | Completar track record, iniciar outreach institucional |
| Mes 3 | Primer piloto enterprise (prop firm o plataforma de trading) |
| Mes 6 | Estructura regulatoria ADGM completa |
| Mes 9 | 3 clientes enterprise pagando |
| Mes 12 | Preparacion para Series A con metricas de revenue validadas |

### El Caso en 60 Segundos

1. **El problema es masivo** — $68B+ perdidos por traders anualmente, cero infraestructura de riesgo accesible
2. **El timing es perfecto** — MiCA + ADGM mandando controles de riesgo AHORA
3. **El producto existe** — No es un slide deck. Corriendo en produccion por 3+ meses.
4. **El enfoque es unico** — Nadie mas optimiza para la contencion
5. **La data es real** — 192,000+ eventos, 98.5% capital preservado, 91% precision de bloqueos
6. **El mercado esta aqui** — Dubai/ADGM es el epicentro de infraestructura crypto institucional

> "La mayoria de los sistemas de trading preguntan: 'Como gano dinero?'
> OMNIX pregunta: 'Como me aseguro de no perderlo?'
> Esa pregunta vale $500K para responderla a escala."

---

## SCRIPT DE PITCH DE 90 SEGUNDOS

*Para practicar la presentacion oral:*

> "El 95% de los sistemas de trading preguntan: 'Cuando deberia entrar al mercado?'
>
> La pregunta correcta es: 'Cuando NO deberia desplegarse capital?'
>
> $68 mil millones — perdidos anualmente por traders a nivel global. Por que? Cero controles de riesgo de grado institucional.
>
> OMNIX es un motor de riesgo fail-closed. Piensa en esto como seguridad de aeropuerto para tu capital. Cada operacion debe sobrevivir 6 checkpoints de seguridad independientes. Un check falla — bloqueo automatico.
>
> Ejemplo real: 3 de febrero. Breakout de BTC — sube 6% en dos horas. Mercado euforico. Los bots tradicionales compraron. OMNIX bloqueo — la tendencia no era sostenida. 48 horas despues, BTC se desplomo 9%. Capital preservado: $50,000.
>
> Hemos analizado 192,000 ciclos de decision. 98.5% de capital preservado. El 91% de los trades bloqueados habrian perdido dinero. Sistema corriendo en produccion 24/7 por tres meses.
>
> Nuestro mercado: prop trading firms, plataformas de trading, fondos regulados — todos necesitan infraestructura de riesgo. 200+ prop firms solo en ADGM y DIFC. Compliance MiCA obligatorio en la UE — 2,000+ plataformas necesitan esto.
>
> Estamos levantando $500K para cerrar 3 pilotos enterprise y establecer nuestra estructura regulatoria en ADGM.
>
> La mejor operacion es, muchas veces, la que no se hace. Eso es lo que construimos.
>
> Preguntas?"

*Tiempo: ~88 segundos*

---

## APENDICE A — DECISION TRACE (Output del Sistema en Vivo)

```json
{
  "timestamp": "2026-02-10T14:23:45Z",
  "symbol": "BTC/USD",
  "decision": "BLOCKED",
  "checkpoints": {
    "probability_check": {
      "win_rate": "48.7%",
      "expected_return": "-0.22%",
      "verdict": "FAIL"
    },
    "risk_limits": {
      "portfolio_exposure": "0%",
      "drawdown_status": "WITHIN_LIMITS",
      "verdict": "PASS"
    },
    "signal_agreement": {
      "consensus": "44%",
      "threshold": "45%",
      "verdict": "FAIL"
    },
    "trend_confirmation": {
      "consecutive_cycles": "0/3",
      "status": "WAITING",
      "verdict": "FAIL"
    },
    "stress_test": {
      "severity": "LOW",
      "crash_probability": "12%",
      "verdict": "PASS"
    },
    "logic_check": {
      "contradiction_index": 62,
      "threshold": 70,
      "verdict": "PASS"
    }
  },
  "final_decision": "BLOCKED — 3 de 6 checkpoints fallaron",
  "capital_preserved": "$47,500"
}
```

> Cada decision que OMNIX toma produce este output. Completamente trazable. Completamente auditable. Nada oculto.

---

## APENDICE B — DOCUMENTOS CLAVE PARA DUE DILIGENCE

| Documento | Descripcion |
|-----------|-------------|
| Executive Fact Sheet | Estado del sistema y marco de gobernanza |
| Track Record Case Study | Narrativa dia a dia de proteccion de capital |
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

**Disclaimer:** Este documento describe actividad de paper trading durante un periodo de validacion. Todas las metricas son de operacion del motor de decision en condiciones reales de mercado. El rendimiento pasado no garantiza resultados futuros. OMNIX es infraestructura de riesgo, no un producto de inversion. Las proyecciones de ingresos son estimaciones basadas en supuestos conservadores.
