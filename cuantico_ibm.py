
# cuantico_ibm.py
import os
from qiskit import QuantumCircuit, transpile, Aer, IBMQ
from qiskit.providers.ibmq import least_busy
from qiskit.visualization import plot_histogram

# Cargar la clave de entorno
IBMQ_API_KEY = os.getenv("IBMQ_API_KEY")

# Inicializar IBMQ
IBMQ.save_account(IBMQ_API_KEY, overwrite=True)
IBMQ.load_account()
provider = IBMQ.get_provider(hub='ibm-q')

# Crear un circuito cuántico básico (Bell State)
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0,1], [0,1])

# Buscar el backend menos ocupado
backend = least_busy(provider.backends(filters=lambda x: x.configuration().n_qubits >= 2 
                                       and not x.configuration().simulator 
                                       and x.status().operational==True))
print(f"Usando backend cuántico real: {backend.name()}")

# Transpilar y ejecutar
transpiled = transpile(qc, backend=backend, optimization_level=1)
job = backend.run(transpiled)
result = job.result()
counts = result.get_counts()

# Resultado final como string
resultado = f"Resultado cuántico en {backend.name()}: {counts}"

# Guardar el resultado para uso en el bot (si se quiere)
with open("resultado_cuantico.txt", "w") as f:
    f.write(resultado)
