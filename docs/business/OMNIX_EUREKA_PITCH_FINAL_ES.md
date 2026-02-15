# OMNIX — Eureka Dubai Pitch Deck
## Version Final para Competencia | Febrero 2026

**Clasificacion**: Listo para Competencia — Revisado por Expertos
**Destino**: Eureka Dubai — Ronda Semifinal

---

## SLIDE 1 — TITULO

**OMNIX**
*Plataforma de Gobernanza de Decisiones con IA*

> "La mejor decision es, muchas veces, la que no se hace."

Harold Nunes — Fundador & Arquitecto de Producto
Pre-Seed | Febrero 2026

contacto@omnixquantum.net | www.omnixquantum.net

---

## SLIDE 2 — EL PROBLEMA (Gancho de 10 Segundos)

**El 95% de los sistemas de decisiones de alto riesgo hacen la pregunta equivocada.**

Preguntan: *"Cuando deberia actuar?"*

La pregunta correcta es:

> **"Cuando NO deberia actuar?"**

**Lo que pasa hoy:**
- Los sistemas automatizados ejecutan constantemente — incluso en condiciones peligrosas
- Sin deteccion de regimen = erosion de capital durante volatilidad
- Controles de riesgo de una sola capa que fallan bajo estres
- $68B+ perdidos anualmente por traders retail a nivel global — y miles de millones mas en malas decisiones en supply chain, credito y seguros

**El resultado:** Los errores costosos son la norma, no la excepcion.

La mayoria de los sistemas optimizan para la *accion*. Nadie optimiza para la *contencion*.

**Primer dominio: Trading de activos digitales.** Pero el problema es universal — cualquier industria donde las decisiones bajo incertidumbre involucran dinero en riesgo.

---

## SLIDE 3 — LA SOLUCION

**OMNIX es una plataforma de gobernanza de decisiones con IA que bloquea errores costosos antes de que sucedan.**

A diferencia de los sistemas que persiguen cada oportunidad, OMNIX opera como un **motor de gobernanza fail-closed**: si la confianza cae por debajo de umbrales definidos, la accion se detiene automaticamente. La misma arquitectura de 6 checkpoints se aplica a cualquier dominio donde las decisiones bajo incertidumbre involucran capital en riesgo.

**Tres Principios:**

| Principio | Que Significa |
|-----------|---------------|
| **Proteccion Antes de Accion** | Prevenir perdidas antes de buscar ganancias. Siempre. |
| **Arquitectura Fail-Closed** | El default = no actuar. Debe ganarse el derecho a ejecutar. |
| **Auditabilidad Total** | Cada decision — ejecutada o bloqueada — queda registrada con justificacion completa. |

**Primera vertical validada: Trading de activos digitales.** La arquitectura es agnostica al dominio — el mismo motor gobierna decisiones en trading, supply chain, credito, seguros y compliance.

> "Saber cuando NO actuar es un edge mas fuerte que forzar la accion."

---

## SLIDE 4 — COMO FUNCIONA (6 Checkpoints de Seguridad)

**Piensa en esto como seguridad de aeropuerto para cada decision de alto riesgo.**

Cada decision debe pasar por 6 checkpoints de seguridad independientes. Si CUALQUIERA falla, la accion se bloquea automaticamente.

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

**LOS 6 deben aprobar — o la accion se bloquea.**

La mayoria de los sistemas tienen 1 control de riesgo. OMNIX tiene 6 independientes que TODOS deben estar de acuerdo. Esta arquitectura es agnostica al dominio — los mismos checkpoints gobiernan decisiones de trading, aprobaciones de compra, extensiones de credito y validaciones de compliance.

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
| **Motor de Gobernanza de 6 Checkpoints** | 5 modelos de IA independientes deben coincidir antes de cualquier accion | Ningun modelo individual puede anular el sistema |
| **Sistema de Memoria Conductual** | Recuerda patrones del mercado mas alla de datos recientes | Ve lo que otros sistemas no ven |
| **Ventana de Confirmacion de Edge** | Requiere persistencia de tendencia por 3 ciclos — no solo un spike | Transforma "preservacion" en "paciencia" |
| **Motor Shadow Portfolio** | Rastrea cada decision vetada para aprender (192,000+ eventos) | El sistema aprende de lo que NO hace |
| **Seguridad Post-Cuantica** | Decisiones firmadas con Dilithium-3 (NIST FIPS 204) | Operacional hoy — no en roadmap |
| **Orquestacion Multi-IA** | Gemini 2.5 Flash + GPT-4o + Claude Sonnet 4 con failover | Cero dependencia de un solo proveedor |

> "Cada decision queda registrada, trazable y revisable. Trail de auditoria — siempre."

---

## SLIDE 8 — VISION MULTI-VERTICAL (Mas Alla del Trading)

**El mismo motor de 6 checkpoints. Diferentes dominios. La misma disciplina.**

OMNIX no es un bot de trading — es una **plataforma de gobernanza de decisiones**. El trading de activos digitales es la primera vertical donde la arquitectura ha sido validada. El mismo motor se aplica donde sea que decisiones de alto riesgo bajo incertidumbre involucren capital en riesgo.

| Vertical | Que Gobierna OMNIX | Ejemplo de Decision |
|----------|-------------------|---------------------|
| **Trading de Activos Digitales** (Validado) | Gobernanza de ejecucion de trades | "Deberia abrirse esta posicion de $50K?" |
| **Supply Chain** | Gobernanza de riesgo de compras | "Deberiamos comprometer $2M en esta orden de proveedor?" |
| **Credito / Prestamos** | Gobernanza de extension de credito | "Deberia aprobarse este prestamo de $500K?" |
| **Seguros** | Gobernanza de suscripcion | "Deberia emitirse esta poliza de alta exposicion?" |
| **Trading de Energia** | Gobernanza de compra de energia | "Deberiamos fijar este contrato de energia?" |
| **RegTech / Compliance** | Gobernanza de compliance operacional | "Esta transaccion viola limites regulatorios?" |

**Por que esto funciona:**

Cada dominio anterior comparte los mismos requisitos fundamentales:
- Multiples senales a evaluar bajo incertidumbre
- Alto costo de decisiones equivocadas
- Necesidad de trails de auditoria y compliance regulatorio
- Beneficio de arquitectura fail-closed (bloquear primero, actuar solo cuando hay confianza)

**La arquitectura de 6 checkpoints es agnostica al dominio.** Los inputs cambian (datos de mercado vs. datos de proveedor vs. scores de credito), pero la logica de gobernanza es identica.

> "Validamos el motor en el dominio mas dificil primero — mercados financieros en tiempo real. Todo lo demas es un conjunto de inputs mas simple."

---

## SLIDE 9 — MODELO DE NEGOCIO (Infraestructura de Gobernanza de Decisiones B2B)

### PRIMARIO: Gobernanza de Decisiones B2B — Licenciamiento a Instituciones

| Tipo de Cliente | Caso de Uso | Precio |
|-----------------|-------------|--------|
| **Prop Trading Firms** (200+ en ADGM/DIFC) | Proteger capital de traders con puertas de riesgo automatizadas | $15K–35K/mes |
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

> "Las instituciones pagan por lo que BLOQUEA malas decisiones, no por alpha."
> Ingreso basado en licencias. Sin tokens. Sin fees de rendimiento.

---

## SLIDE 10 — OPORTUNIDAD DE MERCADO

### Los Numeros

| Mercado | Tamano |
|---------|--------|
| Volumen diario global de trading crypto | **$2.3T+** |
| Mercado de trading algoritmico | **$18.8B** (creciendo 12% CAGR) |
| Prop firms solo en ADGM/DIFC | **200+** |
| Plataformas que necesitan compliance MiCA (2025+) | **2,000+** |
| Objetivo Ano 1 | **3 pilotos enterprise** |

### La Brecha Que Nadie Esta Llenando

La gobernanza de decisiones de grado institucional existe — dentro de hedge funds con $100M+ AUM. NO hay infraestructura de gobernanza accesible para:

- Prop trading firms que necesitan proteger capital de traders
- Plataformas de trading agregando gobernanza de riesgo para compliance
- Fondos regulados (ADGM, DIFC, MiCA) que necesitan trails de auditoria
- Family offices entrando a crypto sin herramientas institucionales
- Operaciones de supply chain y credito que necesitan controles de riesgo automatizados

### Por Que Ahora — Dos Fuerzas Convergiendo

1. **Capital institucional esta inundando activos digitales** — pero sin infraestructura de gobernanza adecuada
2. **Regulacion MiCA (EU) + requisitos ADGM** — las plataformas DEBEN tener gobernanza de decisiones y trails de auditoria

### Expansion de Mercado Multi-Vertical

| Vertical | Mercado Direccionable | Cronograma |
|----------|----------------------|------------|
| Trading de Activos Digitales (Actual) | $18.8B trading algoritmico | Ahora (validado) |
| Riesgo de Supply Chain | $3.2B analitica de supply chain | Ano 2-3 |
| Gobernanza de Credito / Prestamos | $7.4B gestion de riesgo crediticio | Ano 2-3 |
| Suscripcion de Seguros | $5.1B insurtech | Ano 3+ |
| Trading de Energia | $2.8B gestion de riesgo energetico | Ano 3+ |

> El mercado necesita infraestructura de gobernanza de decisiones. No mas senales de trading.
> El reloj regulatorio esta corriendo — y OMNIX esta listo.

---

## SLIDE 11 — POR QUE DUBAI Y MENA

**Alineacion estrategica con la vision de la region:**

| Factor | Por Que Importa |
|--------|-----------------|
| **ADGM** | Marco regulatorio de clase mundial para activos digitales |
| **Capital soberano** | Desplegando activamente en fintech e IA |
| **DIFC** | Acceso directo a red de inversores institucionales |
| **Hub71** | Aplicacion enviada — pendiente de respuesta (aceleradora de innovacion) |
| **200+ prop firms** | Mercado direccionable inmediato en la region |
| **Posicion geografica** | Puente entre Asia, Europa y Africa |
| **Sofisticacion de inversores** | Asignadores de capital que valoran disciplina sobre hype |

**OMNIX esta construido para entornos regulados.** La transicion del "salvaje oeste crypto" a infraestructura de grado institucional esta sucediendo aqui primero.

---

## SLIDE 12 — FUNDADOR Y EQUIPO

**Harold Nunes**
*Fundador & Arquitecto de Producto*

- Construyo OMNIX desde concepto hasta sistema corriendo en produccion
- Diseno el motor de seguridad de 6 checkpoints, logica de riesgo y orquestacion de IA
- Tecnologo autodidacta con disciplina de finanzas institucionales
- Reubicandose a Dubai para ecosistema ADGM

**Ivan David Guzman Ruiz**
*Software Engineer*

- Contribuidor clave en la ingenieria e infraestructura de produccion de OMNIX
- Instrumental en llevar arquitectura de grado profesional a la plataforma

**Estructura Actual:**
- Arquitectura core, logica de riesgo y roadmap: Liderado por el fundador
- Ingenieria e infraestructura de produccion: Equipo core de 2 personas
- Ecosistema: Aplicacion a Hub71 (pendiente), construyendo red en ADGM/DIFC

**Por Que Funciona:**
- Velocidad de ejecucion sobre tamano del equipo — producto ya corriendo 24/7
- Validacion en mercado real desde el dia uno — no investigacion teorica
- La ronda de $500K incluye 2-3 contrataciones adicionales de ingenieria para API enterprise

**LinkedIn:** linkedin.com/in/harold-nunes-21bb65285

---

## SLIDE 13 — EL ASK

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

1. **El problema es masivo** — $68B+ perdidos por traders anualmente, miles de millones mas en malas decisiones en multiples industrias
2. **El timing es perfecto** — MiCA + ADGM mandando gobernanza de decisiones AHORA
3. **El producto existe** — No es un slide deck. Corriendo en produccion por 3+ meses.
4. **El enfoque es unico** — Nadie mas optimiza para la contencion
5. **La data es real** — 192,000+ decisiones gobernadas, 98.5% capital preservado, 91% precision de bloqueos
6. **El mercado esta aqui** — Dubai/ADGM es el epicentro de infraestructura de gobernanza institucional
7. **La vision escala** — Mismo motor, multiples verticales: trading, supply chain, credito, seguros

> "La mayoria de los sistemas de decisiones preguntan: 'Como maximizo retornos?'
> OMNIX pregunta: 'Como me aseguro de que los errores costosos no sucedan?'
> Esa pregunta vale $500K para responderla a escala."

---

## SCRIPT DE PITCH DE 90 SEGUNDOS

*Para practicar la presentacion oral:*

> "El 95% de los sistemas de decisiones de alto riesgo preguntan: 'Cuando deberia actuar?'
>
> La pregunta correcta es: 'Cuando NO deberia actuar?'
>
> $68 mil millones — perdidos anualmente solo por traders. Miles de millones mas en malas decisiones de compras, credito y seguros. Por que? Cero gobernanza de decisiones de grado institucional.
>
> OMNIX es una plataforma de gobernanza de IA fail-closed. Piensa en esto como seguridad de aeropuerto para cada decision de alto riesgo. Cada accion debe sobrevivir 6 checkpoints independientes antes de ejecutarse. Un check falla — bloqueo automatico.
>
> Validamos esto en el dominio mas dificil primero — mercados financieros en tiempo real. Ejemplo real: 3 de febrero. Breakout de BTC — sube 6% en dos horas. Mercado euforico. Los bots tradicionales compraron. OMNIX bloqueo — la tendencia no era sostenida. 48 horas despues, BTC se desplomo 9%. Capital preservado: $50,000.
>
> 192,000 decisiones gobernadas. 98.5% de capital preservado. El 91% de las acciones bloqueadas habrian resultado en perdidas. Sistema corriendo en produccion 24/7 por tres meses.
>
> Nuestro primer mercado: prop trading firms, plataformas de trading, fondos regulados. 200+ prop firms solo en ADGM y DIFC. Pero el mismo motor se aplica a supply chain, credito, seguros y compliance.
>
> Estamos levantando $500K para cerrar 3 pilotos enterprise en activos digitales y comenzar la expansion multi-vertical.
>
> La mejor decision es, muchas veces, la que no se hace. Eso es lo que construimos.
>
> Preguntas?"

*Tiempo: ~90 segundos*

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

*OMNIX — Gobernando Decisiones Bajo Incertidumbre*
*Eureka Dubai 2026 — Semifinalista*

---

**Disclaimer:** Este documento describe la operacion del motor de gobernanza de decisiones durante un periodo de validacion utilizando trading de activos digitales como primera vertical. Todas las metricas son de operacion del motor de decision en condiciones reales de mercado. El rendimiento pasado no garantiza resultados futuros. OMNIX es infraestructura de gobernanza de decisiones, no un producto de inversion. Las proyecciones de ingresos son estimaciones basadas en supuestos conservadores. Los cronogramas de expansion multi-vertical son proyecciones, no compromisos.
