# OMNIX — Simulación de Q&A para Eureka Dubai 2026
## Drill Interactivo — 3 Jueces, 12 Preguntas + Follow-ups de Presión

**Propósito:** Practicar como si estuvieras en el escenario. Cada pregunta incluye el contexto del juez, la respuesta ideal (máximo 30 segundos), el follow-up de presión, y cómo manejarlo.

**Regla de oro:** Número primero. Siempre. Luego explicas.

---

## JUEZ 1 — EL TÉCNICO
**Perfil:** CTO, ex-quant, o ingeniero de sistemas. No le impresionan las palabras — quiere ver que entiendes lo que construiste. Si detecta que estás improvisando, te destruye.

**Su objetivo oculto:** Verificar que no es un demo de PowerPoint. Quiere saber si el sistema realmente funciona o si es humo.

---

### T1. "¿Cómo funciona tu Monte Carlo? ¿Qué distribuyes exactamente?"

🎯 **Lo que realmente pregunta:** ¿Sabes matemáticas o solo usas el nombre?

✅ **Respuesta ideal (30 seg):**
> "Ejecutamos 10,000 simulaciones por ciclo de decisión. Distribución de retornos históricos del activo con cola pesada — no normal, para capturar eventos extremos. El resultado: win rate esperado y retorno esperado. Si el win rate es menor al 50% o el retorno esperado es negativo, el sistema veta automáticamente — no importa cuánto diga el resto del modelo. Es el primer checkpoint de los seis."

🪤 **Follow-up trampa:** *"¿Por qué 10,000 y no 1,000 o 100,000? ¿Cuánto tarda cada ciclo?"*

🛡️ **Cómo manejar:**
> "10,000 es el balance entre precisión estadística y latencia. A 1,000 el error estándar es demasiado alto. A 100,000 la latencia supera la ventana de trading. Cada ciclo completo — incluyendo los seis checkpoints — tarda entre 8 y 15 segundos en producción. Para governance esto es aceptable; no somos un sistema de alta frecuencia."

---

### T2. "¿Qué es el Non-Markovian Memory Kernel y por qué es mejor que un modelo estándar?"

🎯 **Lo que realmente pregunta:** ¿Usas buzzwords o hay sustancia?

✅ **Respuesta ideal (30 seg):**
> "Un modelo Markoviano asume que el siguiente estado depende solo del estado actual. Los mercados no funcionan así — el contexto histórico importa. Nuestro Memory Kernel pondera el historial de decisiones del sistema: cuántas veces se vetó en condiciones similares, con qué resultado. No es deep learning — es memoria condicional ponderada. Aporta 15 puntos al scoring de 100 del sistema."

🪤 **Follow-up trampa:** *"¿Por qué no usas simplemente un LSTM o una red recurrente para eso?"*

🛡️ **Cómo manejar:**
> "Podríamos. Pero una LSTM requiere re-entrenamiento con datos etiquetados y produce una caja negra. Nuestro kernel es interpretable — puedo explicar exactamente por qué el sistema recuerda que las últimas tres señales similares fueron bloqueadas correctamente. En governance, la explicabilidad no es opcional. Un regulador o un cliente institucional necesita saber por qué se tomó cada decisión."

---

### T3. "20,610 receipts PQC — ¿qué firma exactamente? ¿La orden de compra o el análisis completo?"

🎯 **Lo que realmente pregunta:** ¿Es real el audit trail o es solo un counter?

✅ **Respuesta ideal (30 seg):**
> "Cada receipt firma el payload completo de la decisión: timestamp, activo, señal, resultado de los 6 checkpoints, scoring final, razón del veto si aplica, y el hash del receipt anterior — formando una cadena hash. La firma usa Dilithium-3, algoritmo NIST-estandardizado post-cuántico. Cualquiera puede verificar cualquier receipt en tiempo real en omnixquantum.net/verify — con la clave pública disponible públicamente."

🪤 **Follow-up trampa:** *"¿Quién verificó externamente que las firmas son válidas? ¿Tienen un audit externo?"*

🛡️ **Cómo manejar:**
> "El sistema de verificación pública es el audit externo accesible. Cualquier auditor puede verificar matemáticamente la integridad de la cadena sin acceder a nuestros sistemas internos — porque la criptografía lo garantiza, no nosotros. Para Fase 2, con los fondos de esta ronda, contrataremos un audit de seguridad formal. El diseño ya está preparado para eso."

---

### T4. "¿Qué pasa si los 5 modelos de IA coinciden en ejecutar pero el mercado está en un régimen peligroso?"

🎯 **Lo que realmente pregunta:** ¿Puede el sistema ser engañado por consensus AI?

✅ **Respuesta ideal (30 seg):**
> "El régimen de mercado se valida antes del scoring de IA. El Monte Carlo veta por condiciones de mercado independientemente del consenso de los modelos. Adicionalmente, el Black Swan Detector puede vetar sin importar cuántos modelos voten por ejecutar. La arquitectura es deliberadamente heterárquica — ningún componente puede ser anulado por el consensus de otro. El modelo de AI con mayor peso vale máximo 40 puntos de 100. No puede ganar solo."

---

## JUEZ 2 — EL FINANCIERO
**Perfil:** VC, angel investor, o banker. Piensa en múltiplos, retorno, y riesgo de inversión. Si los números no tienen sentido, no importa la tecnología.

**Su objetivo oculto:** Encontrar el agujero en la valoración o en el modelo de negocio. Busca por qué NO invertir.

---

### F1. "Pre-money de $2.5M-$3M para una empresa pre-revenue. Justifícame eso."

🎯 **Lo que realmente pregunta:** ¿Estás inventando el número o hay lógica?

✅ **Respuesta ideal (30 seg):**
> "Tres factores. Primero: el producto existe y corre en producción 24/7 desde noviembre 2025 — esto no es un concepto. Segundo: 681,000+ eventos de datos validando la arquitectura, con audit trail criptográfico público. Tercero: comparables de mercado — Chainalysis levantó a $4M pre-money en una etapa comparable. Con MiCA creando demanda obligatoria de governance infrastructure para 2,000+ plataformas en Europa, $2.5M es conservador."

🪤 **Follow-up trampa:** *"Chainalysis es blockchain analytics, no trading governance. No es comparable."*

🛡️ **Cómo manejar:**
> "Correcto — el comparable no es el producto, es la etapa y el tipo de infraestructura. Chainalysis es infraestructura de compliance para crypto. OMNIX es infraestructura de governance para decisiones automatizadas. Ambos son B2B infrastructure plays con contratos institucionales y alta retención. El múltiplo de infraestructura en fintech — según Bessemer — es típicamente 8-12x ARR. Con tres pilotos a $25K/mes en Año 1, eso es $900K ARR y una valoración de $7-11M. La entrada a $2.5M pre-money da 3-4x en Año 1 si ejecutamos."

---

### F2. "Perdieron $15,198 en la fase de calibración. ¿Por qué debería invertir en un sistema que pierde dinero?"

🎯 **Lo que realmente pregunta:** ¿Puedes defender una pérdida o te pones nervioso?

✅ **Respuesta ideal (30 seg):**
> "Esa pérdida fue intencional y documentada. Fue el costo de calibración — 119 trades en condiciones reales para ajustar 6 checkpoints a datos de mercado live. Ningún sistema de governance nace calibrado. Desde el 15 de enero, el sistema opera con los parámetros recalibrados: 98.5% de capital preservado durante un período en que Bitcoin cayó 7.37%. La pregunta correcta no es '¿por qué perdieron $15K?' — es '¿cuánto habrían perdido sin el sistema en ese mismo período?'"

🪤 **Follow-up trampa:** *"¿Y por qué no tienen más trades en el Track Record Oficial? Cero trades en 6 semanas suena a que el sistema está demasiado conservador para ser útil."*

🛡️ **Cómo manejar:**
> "El sistema bloqueó durante ese período porque las condiciones de mercado no pasaron los 6 checkpoints. Bitcoin estuvo en un régimen de alta volatilidad. Un sistema de governance que ejecuta en cualquier condición no es un sistema de governance — es un sistema de trading normal. El valor es precisamente que sabe cuándo NO ejecutar. Si en ese período hubiéramos forzado trades, habríamos perdido capital. En cambio, preservamos el 98.5%."

---

### F3. "TAM de $37B. Todo el mundo dice que su TAM es enorme. ¿Cuál es tu SAM real en Año 1?"

🎯 **Lo que realmente pregunta:** ¿Tienes un plan real o solo slides?

✅ **Respuesta ideal (30 seg):**
> "SAM Año 1: 200+ prop firms en ADGM y DIFC. Precio objetivo: $15K-$25K por mes. Si cerramos 3 pilotos a $20K promedio, eso es $720K ARR. Ese es nuestro objetivo de Año 1 — no el TAM. El TAM de $37B es el mercado de software de risk management donde jugamos a largo plazo. Nuestro SOM de Año 1 es $720K. Nuestro SOM de Año 3 con 5 verticales es $4-8M ARR. Lo que pedimos hoy financia llegar al primero de esos números."

🪤 **Follow-up trampa:** *"¿Tienes LOIs o pilots firmados ya?"*

🛡️ **Cómo manejar:**
> "No tenemos LOIs firmados hoy — y sería engañoso decir que sí. Lo que tenemos es: el producto funcionando, la credencial de Eureka Semifinalist para abrir puertas en Dubai, y conversaciones activas. El capital de esta ronda incluye 20% asignado a business development desde el Mes 3. Parte del trabajo de los próximos 90 días es convertir esas conversaciones en contratos firmados."

---

### F4. "¿Cuál es tu plan si en 18 meses no tienes revenue? ¿Puentes? ¿Dilución?"

🎯 **Lo que realmente pregunta:** ¿Sabes gestionar un runway o eres ingenuo con el dinero?

✅ **Respuesta ideal (30 seg):**
> "El runway de $500K nos da 18 meses con burn de $27K/mes. Ese breakdown es: 40% engineering ($200K, 2 hires), 25% legal/regulatorio ADGM ($125K), 20% BD ($100K), 15% ops ($75K). Si a mes 12 no tenemos revenue, las opciones son: reducir burn a $15K/mes cortando en ops, explorar un strategic angel en Dubai (la red de Eureka facilita eso), o levantar un puente de $150K-$200K para llegar a Series A. Pero el modelo base — 3 pilotos en 12 meses — está diseñado para que no lleguemos a ese escenario."

---

## JUEZ 3 — EL HUMANO
**Perfil:** Entrepreneur experimentado, mentor, o juez del ecosistema startup. Le importa menos la tecnología y más la persona. ¿Puede este founder ejecutar? ¿Por qué él?

**Su objetivo oculto:** Detectar si el founder tiene la madera para superar adversidad. Busca autenticidad — detecta a los que memorizaron respuestas de Google.

---

### H1. "¿Por qué tú? ¿Qué te hace la persona correcta para construir esto?"

🎯 **Lo que realmente pregunta:** ¿Hay fuego real aquí o es un proyecto de CV?

✅ **Respuesta ideal (30 seg):**
> "Porque construí esto como respuesta a haber visto — de primera mano — cómo sistemas automatizados toman decisiones sin ninguna capa de governance. No viene de un curso o de un paper académico. Viene de operar con capital real, perder dinero real en la fase de calibración, y usar esa experiencia para construir la infraestructura que necesitaba pero no existía. Hay 27 Architecture Decision Records que documentan cada decisión técnica que tomé. Eso no se hace para un demo — se hace cuando construyes algo que importa."

🪤 **Follow-up trampa:** *"Pero no tienes background en fintech institutional. ¿Por qué confiaría un prop firm en ti?"*

🛡️ **Cómo manejar:**
> "La pregunta correcta es: ¿confiaría en el sistema? El sistema genera un audit trail criptográfico verificable públicamente — no tienes que confiar en mí, puedes verificar cada decisión matemáticamente. Y para el componente de confianza humana: los primeros clientes no serán los 20 traders más grandes de ADGM — serán los que tienen el problema más urgente y menos recursos para resolverlo internamente. Ahí es donde el track record habla."

---

### H2. "Construiste esto solo. ¿Cuál fue el momento más difícil y qué aprendiste?"

🎯 **Lo que realmente pregunta:** ¿Eres resiliente o te rindes cuando algo sale mal?

✅ **Respuesta ideal (30 seg):**
> "El momento más difícil fue la fase de calibración — perder $15,000 mientras el sistema estaba aprendiendo. Lo peor no fue el dinero. Fue darme cuenta de que tenía 6 checkpoints pero los parámetros estaban mal calibrados. Tuve dos opciones: parar o recalibrar con los datos reales. Elegí recalibrar. Lo que aprendí: en sistemas de governance, el fracaso controlado es parte del diseño — si tu sistema no puede aprender de sus errores, no puede proteger de los errores de otros."

🪤 **Follow-up trampa:** *"¿No te desmotivaste después de perder ese dinero?"*

🛡️ **Cómo manejar:**
> "No — me confirmó que el problema que estoy resolviendo es real. Si el sistema hubiera sido perfecto desde el día 1, estaría vendiendo algo que no necesita existir. Los $15K de calibración son los datos más valiosos que tengo — son la prueba de que el sistema aprende en condiciones reales. Ningún backtest te da eso."

---

### H3. "Si Eureka no resulta en funding, ¿qué haces mañana?"

🎯 **Lo que realmente pregunta:** ¿Dependes de este concurso o tienes convicción independiente?

✅ **Respuesta ideal (30 seg):**
> "El sistema sigue corriendo mañana. El bot sigue en producción. Los 681,000 ciclos siguen acumulándose. Lo que Eureka hace es acelerar — abre puertas en Dubai que tomarían 18 meses abrir de otra forma. Si no resulta aquí, el siguiente paso es una ronda ángel directa con los contactos del ecosistema ADGM. El producto no depende del concurso para existir — el concurso acelera la go-to-market."

🪤 **Follow-up trampa:** *"Eso suena a que no necesitas el dinero. ¿Para qué estás aquí entonces?"*

🛡️ **Cómo manejar:**
> "Lo necesito — pero no desesperadamente. Hay diferencia. El capital acelera en 18 meses lo que sin él tarda 36. Lo que no haría es levantar a cualquier condición o comprometer el control del producto. Eureka es el mejor escenario porque combina capital con red de Dubai con validación de jueces con expertise real. Eso es difícil de replicar."

---

### H4. "¿En 5 años, qué es OMNIX?"

🎯 **Lo que realmente pregunta:** ¿Tienes visión o solo estás haciendo un proyecto de trading?

✅ **Respuesta ideal (30 seg):**
> "En 5 años, OMNIX es la infraestructura de governance que corre debajo de decisiones automatizadas en 4-5 industrias. Trading fue el primer vertical porque es donde el costo de una mala decisión es inmediato y medible. Pero el mismo problema existe en lending automatizado, en seguros, en supply chain, en sistemas de IA médica. La pregunta en todos esos casos es la misma: ¿cómo sabes cuándo el sistema automatizado NO debería actuar? Eso es OMNIX — no un bot de trading, sino la capa de governance que hace que los sistemas automatizados sean confiables."

🪤 **Follow-up trampa:** *"Eso es muy ambicioso para un solo founder. ¿No es mejor enfocarte solo en trading?"*

🛡️ **Cómo manejar:**
> "El enfoque de Año 1 es 100% trading — tres pilotos en ADGM. La arquitectura domain-agnostic no es una promesa de Año 5, es una consecuencia del diseño de Año 1. Construí los 6 checkpoints sin hardcodear lógica de trading — es governance logic. Si hubiera construido un sistema de trading, estaría compitiendo con 3Commas. Construí infraestructura de governance que hoy se aplica a trading. La expansión no requiere reconstruir — requiere re-parametrizar."

---

## REGLAS DE ENTREGA EN ESCENARIO

| Situación | Respuesta |
|-----------|-----------|
| Pregunta que no esperabas | "Déjame asegurarme de responder exactamente lo que preguntas..." (ganas 3 segundos, no lo inventas) |
| Número que no recuerdas | "El dato exacto está en el data room — lo que sé con certeza es..." |
| Ataque personal al founder | No te defiendas — responde con datos del sistema |
| Silencio incómodo del juez | No lo llenes. Deja que la respuesta se asiente. |
| "¿Eso es todo?" | "Sí. ¿Quieres que profundice en algún punto específico?" |

---

## LOS 3 ERRORES MÁS COMUNES EN PITCH Q&A

1. **Empezar con "Buena pregunta"** — Nunca. Directamente al número.
2. **Disculparse por una debilidad** — En su lugar, enmarca la debilidad como una decisión. "No tenemos LOIs porque priorizamos que el producto funcionara primero."
3. **Dar respuestas más largas bajo presión** — La presión del juez es una trampa para hacerte hablar de más. Respuesta más corta = más confianza.

---

## SIMULACIÓN RÁPIDA — 5 MINUTOS ANTES DEL PITCH

Léete estas 3 preguntas en voz alta y respóndelas sin mirar las respuestas:

1. "¿Cuántos trades reales ejecutaron?"
2. "¿Por qué $2.5M pre-money?"
3. "¿Qué haces si no levantas funding?"

Si puedes responder las tres en menos de 90 segundos totales, estás listo.

---

*OMNIX — Governing Decisions Under Uncertainty*
*Eureka Dubai 2026 — Semifinalista*
*Deadline: 15 de marzo, 2026*
