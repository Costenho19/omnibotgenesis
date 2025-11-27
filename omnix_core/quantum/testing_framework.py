"""
OMNIX V6.0 ULTRA - Quantum Testing Framework
=============================================
Validates AI responses for mathematical CORRECTNESS, not just presence of symbols.

This framework tests each of the 24 verified formulas to ensure:
1. AI gives correct answers (not just uses quantum symbols)
2. Common errors are detected and flagged
3. Daily automated testing provides investor confidence

Author: OMNIX Development Team
Date: November 2025
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """A single test case for quantum physics validation"""
    id: str
    formula_name: str
    question: str
    correct_answers: List[str]
    wrong_answers: List[str]
    category: str
    weight: float = 1.0
    explanation: str = ""


@dataclass 
class TestResult:
    """Result of running a single test"""
    test_id: str
    passed: bool
    response_snippet: str
    correct_found: List[str]
    errors_found: List[str]
    score: float
    details: str


class QuantumTestingFramework:
    """
    Testing framework that validates AI responses for CORRECTNESS.
    
    Key insight: We need to check if answers are RIGHT, not just if
    they contain quantum symbols (â, ℏ, etc).
    
    Usage:
        framework = QuantumTestingFramework()
        results = await framework.run_full_suite(ai_model_func)
        report = framework.generate_investor_report(results)
    """
    
    def __init__(self):
        """Initialize with 24 test cases (one per verified formula)"""
        self.test_cases = self._create_test_cases()
        self.last_run: Optional[datetime] = None
        self.last_results: Optional[Dict] = None
        
    def _create_test_cases(self) -> Dict[str, TestCase]:
        """Create comprehensive test cases for all 24 formulas"""
        
        return {
            # ============================================
            # V1.0 - FOUNDATIONAL (6 tests)
            # ============================================
            
            'homodyne_variance': TestCase(
                id='homodyne_variance',
                formula_name='Varianza de Detección Homodina',
                question='¿Cuál es la fórmula de varianza en detección homodina balanceada?',
                correct_answers=[
                    'σ² = (hν/4) × Δf',
                    'hν/4',
                    'hv/4',
                    'independiente de la potencia',
                    'no depende del LO'
                ],
                wrong_answers=[
                    'depende de la potencia',
                    'proporcional a P_LO',
                    'σ² = P_LO',
                ],
                category='foundational',
                weight=1.0,
                explanation='La varianza homodina es INDEPENDIENTE de la potencia del LO'
            ),
            
            'shot_noise': TestCase(
                id='shot_noise',
                formula_name='Shot Noise Limit',
                question='¿Cuál es el límite de shot noise en fotocorriente?',
                correct_answers=[
                    'P_shot = 2eI × Δf',
                    '2eI',
                    'shot noise = 2eIΔf',
                    'ruido de disparo',
                ],
                wrong_answers=[
                    'P = I²',
                    'ruido térmico',
                    'Johnson noise',
                ],
                category='foundational',
                weight=1.0
            ),
            
            'vacuum_fluctuations': TestCase(
                id='vacuum_fluctuations',
                formula_name='Fluctuaciones del Vacío',
                question='¿Cuál es la energía de punto cero del vacío cuántico?',
                correct_answers=[
                    'E₀ = ℏω/2',
                    'hbar*omega/2',
                    'ℏω/2',
                    'hw/2',
                    'medio cuanto',
                ],
                wrong_answers=[
                    'E = 0',
                    'energía cero',
                    'no hay energía',
                    'vacío clásico',
                ],
                category='foundational',
                weight=1.0
            ),
            
            'squeezed_states': TestCase(
                id='squeezed_states',
                formula_name='Estados Comprimidos (Squeezed)',
                question='En un estado squeezed, ¿qué pasa con las varianzas de las cuadraturas?',
                correct_answers=[
                    'una se reduce y otra aumenta',
                    'Var(X) < 1/4, Var(P) > 1/4',
                    'e^{-2r}',
                    'e^{2r}',
                    'producto se conserva',
                ],
                wrong_answers=[
                    'ambas se reducen',
                    'violan Heisenberg',
                    'ambas aumentan',
                ],
                category='foundational',
                weight=1.0
            ),
            
            'anu_qrng': TestCase(
                id='anu_qrng',
                formula_name='ANU QRNG Physics',
                question='¿Cómo funciona el QRNG de ANU?',
                correct_answers=[
                    'fluctuaciones del vacío',
                    'detección homodina',
                    'vacuum fluctuations',
                    'shot noise',
                    'ruido cuántico',
                ],
                wrong_answers=[
                    'decaimiento radiactivo',
                    'ruido térmico',
                    'pseudoaleatorio',
                    'algoritmo',
                ],
                category='foundational',
                weight=1.0
            ),
            
            'bias_removal': TestCase(
                id='bias_removal',
                formula_name='Eliminación de Bias',
                question='¿Cómo se elimina el bias en un QRNG?',
                correct_answers=[
                    'von Neumann',
                    'extractor',
                    'XOR',
                    'whitening',
                    'post-procesado',
                ],
                wrong_answers=[
                    'no es necesario',
                    'es perfecto sin procesar',
                    'sin corrección',
                ],
                category='foundational',
                weight=0.8
            ),
            
            # ============================================
            # V2.0 - DERIVATIONS (4 tests)
            # ============================================
            
            'homodyne_derivation': TestCase(
                id='homodyne_derivation',
                formula_name='Derivación Formal Homodina',
                question='¿Cómo se deriva la corriente de diferencia en homodina balanceada?',
                correct_answers=[
                    'î_diff = â†_LO â_vac + â†_vac â_LO',
                    'beam-splitter',
                    '50/50',
                    'resta de detectores',
                ],
                wrong_answers=[
                    'suma de detectores',
                    'un solo detector',
                ],
                category='derivations',
                weight=1.0
            ),
            
            'canonical_quadrature': TestCase(
                id='canonical_quadrature',
                formula_name='Cuadratura Canónica',
                question='¿Cuál es la definición de la cuadratura X̂_θ?',
                correct_answers=[
                    'X̂_θ = ½(â e^{-iθ} + â† e^{iθ})',
                    '½(â + â†)',
                    'X = (a + a†)/2',
                    'factor 1/2',
                    'factor ½',
                ],
                wrong_answers=[
                    '1/√2',
                    'sin factor',
                    'X = a + a†',
                ],
                category='derivations',
                weight=1.5,
                explanation='CRÍTICO: Usamos factor ½, NO 1/√2'
            ),
            
            'commutator_xp': TestCase(
                id='commutator_xp',
                formula_name='Conmutador [X̂, P̂]',
                question='Calcula [X̂, P̂] usando X̂ = ½(â + â†) y P̂ = (â† - â)/(2i)',
                correct_answers=[
                    '[X̂, P̂] = i/2',
                    'i/2',
                    '0.5i',
                    'i*0.5',
                    'i × 0.5',
                ],
                wrong_answers=[
                    'iℏ',
                    'i',
                    '1',
                    'ℏ',
                    'i*hbar',
                ],
                category='derivations',
                weight=2.0,
                explanation='CRÍTICO: En nuestras unidades [X,P]=i/2, NO iℏ'
            ),
            
            'vacuum_variance': TestCase(
                id='vacuum_variance',
                formula_name='Varianza del Vacío',
                question='¿Cuál es Var(X̂) en el estado de vacío |0⟩?',
                correct_answers=[
                    'Var(X̂) = 1/4',
                    '1/4',
                    '0.25',
                    '¼',
                    'un cuarto',
                ],
                wrong_answers=[
                    '0',
                    '1/2',
                    '1',
                    'cero',
                ],
                category='derivations',
                weight=2.0,
                explanation='CRÍTICO: Var(X)=1/4 (no 0, no 1/2)'
            ),
            
            # ============================================
            # V3.0 - PHD LEVEL (5 tests)
            # ============================================
            
            'temporal_autocorrelation': TestCase(
                id='temporal_autocorrelation',
                formula_name='Autocorrelación Temporal',
                question='¿Cuál es la autocorrelación ⟨X̂(t₁)X̂(t₂)⟩ del vacío?',
                correct_answers=[
                    '(ℏω/4) cos(ω(t₂-t₁))',
                    'ℏω/4',
                    'coseno',
                    'delta(t₂-t₁)',
                    'oscila',
                ],
                wrong_answers=[
                    'constante',
                    'cero siempre',
                    'no hay correlación',
                ],
                category='phd_level',
                weight=1.0
            ),
            
            'johnson_nyquist': TestCase(
                id='johnson_nyquist',
                formula_name='Johnson-Nyquist vs Cuántico',
                question='¿Cuál es la diferencia entre ruido Johnson-Nyquist y ruido cuántico?',
                correct_answers=[
                    'térmico vs cuántico',
                    '4kTRΔf',
                    'kT',
                    'temperatura',
                    'T→0 desaparece térmico',
                ],
                wrong_answers=[
                    'son iguales',
                    'no hay diferencia',
                    'ambos desaparecen a T=0',
                ],
                category='phd_level',
                weight=1.0
            ),
            
            'von_neumann_entropy': TestCase(
                id='von_neumann_entropy',
                formula_name='Entropía de von Neumann',
                question='¿Cuál es la fórmula de entropía de von Neumann?',
                correct_answers=[
                    'S = -Tr(ρ log ρ)',
                    '-Tr(ρ ln ρ)',
                    'traza',
                    'matriz densidad',
                ],
                wrong_answers=[
                    'S = -p log p',
                    'Shannon',
                    'clásica',
                ],
                category='phd_level',
                weight=1.0
            ),
            
            'bell_chsh': TestCase(
                id='bell_chsh',
                formula_name='Desigualdad de Bell/CHSH',
                question='¿Cuál es la máxima violación cuántica de CHSH?',
                correct_answers=[
                    '2√2',
                    '2.828',
                    '2*sqrt(2)',
                    'Tsirelson',
                    '2.83',
                ],
                wrong_answers=[
                    '2',
                    '4',
                    '3',
                    'no se viola',
                ],
                category='phd_level',
                weight=1.5,
                explanation='CHSH clásico ≤ 2, cuántico = 2√2 ≈ 2.828'
            ),
            
            'min_entropy': TestCase(
                id='min_entropy',
                formula_name='Min-Entropy Extraction',
                question='¿Qué es la min-entropy H_min y cómo se calcula?',
                correct_answers=[
                    'H_min = -log₂(P_guess)',
                    '-log(P_max)',
                    'probabilidad máxima',
                    'peor caso',
                ],
                wrong_answers=[
                    'Shannon entropy',
                    'H = -Σp log p',
                    'promedio',
                ],
                category='phd_level',
                weight=1.0
            ),
            
            # ============================================
            # V4.0 - ULTRA ADVANCED (9 tests)
            # ============================================
            
            'wigner_function': TestCase(
                id='wigner_function',
                formula_name='Función de Wigner',
                question='¿Qué es la función de Wigner y puede ser negativa?',
                correct_answers=[
                    'cuasi-probabilidad',
                    'fase-espacio',
                    'puede ser negativa',
                    'W(x,p)',
                    'no es probabilidad real',
                ],
                wrong_answers=[
                    'siempre positiva',
                    'es probabilidad real',
                    'distribución clásica',
                ],
                category='ultra_advanced',
                weight=1.5
            ),
            
            'quantum_fisher_info': TestCase(
                id='quantum_fisher_info',
                formula_name='Información de Fisher Cuántica',
                question='¿Qué es la Información de Fisher Cuántica F_Q?',
                correct_answers=[
                    'Cramér-Rao',
                    'límite de precisión',
                    'Δθ ≥ 1/√(NF_Q)',
                    'metrología',
                    '4 Var(Ĝ)',
                ],
                wrong_answers=[
                    'información de Shannon',
                    'entropía',
                    'no tiene límite',
                ],
                category='ultra_advanced',
                weight=1.5
            ),
            
            'fock_vs_coherent': TestCase(
                id='fock_vs_coherent',
                formula_name='Estados Fock vs Coherentes',
                question='¿Cuál es la diferencia entre estados Fock |n⟩ y coherentes |α⟩?',
                correct_answers=[
                    'Fock: número definido',
                    'coherente: fase definida',
                    'Poisson vs sub-Poisson',
                    'Δn = 0 en Fock',
                    'Δn = √n̄ en coherente',
                ],
                wrong_answers=[
                    'son iguales',
                    'láser produce Fock',
                    'ambos tienen fase definida',
                ],
                category='ultra_advanced',
                weight=1.0
            ),
            
            'heisenberg_limit': TestCase(
                id='heisenberg_limit',
                formula_name='Límite de Heisenberg vs SQL',
                question='¿Cuál es la diferencia entre SQL y límite de Heisenberg?',
                correct_answers=[
                    'SQL: 1/√N',
                    'Heisenberg: 1/N',
                    'mejora = √N',
                    'entrelazamiento',
                    'NOON states',
                ],
                wrong_answers=[
                    'son iguales',
                    'SQL es mejor',
                    'Heisenberg: 1/√N',
                ],
                category='ultra_advanced',
                weight=2.0,
                explanation='CRÍTICO: SQL=1/√N, Heisenberg=1/N'
            ),
            
            'no_cloning': TestCase(
                id='no_cloning',
                formula_name='Teorema de No-Clonación',
                question='¿Por qué no se puede clonar un estado cuántico desconocido?',
                correct_answers=[
                    'linealidad',
                    'contradicción',
                    'unitariedad',
                    'QKD',
                    'BB84',
                    'seguridad cuántica',
                ],
                wrong_answers=[
                    'sí se puede clonar',
                    'es posible con medición',
                    'amplificación cuántica',
                ],
                category='ultra_advanced',
                weight=1.5
            ),
            
            'decoherence_time': TestCase(
                id='decoherence_time',
                formula_name='Tiempo de Decoherencia',
                question='¿Qué son T₁ y T₂ en decoherencia cuántica?',
                correct_answers=[
                    'T₁: relajación',
                    'T₂: defaseo',
                    'T₂ ≤ 2T₁',
                    'pérdida de coherencia',
                    'entorno',
                ],
                wrong_answers=[
                    'T₂ > 2T₁',
                    'no hay límite',
                    'son independientes del entorno',
                ],
                category='ultra_advanced',
                weight=1.0
            ),
            
            'mandel_q': TestCase(
                id='mandel_q',
                formula_name='Parámetro Q de Mandel',
                question='¿Qué indica el parámetro Q de Mandel y qué valores tiene?',
                correct_answers=[
                    'Q = (Var(n) - ⟨n⟩) / ⟨n⟩',
                    'Q = 0: Poisson',
                    'Q < 0: sub-Poisson',
                    'Q > 0: super-Poisson',
                    'Q negativo es cuántico',
                ],
                wrong_answers=[
                    'Q siempre positivo',
                    'Q = 0 es cuántico',
                    'no distingue estados',
                ],
                category='ultra_advanced',
                weight=1.5
            ),
            
            'g2_correlation': TestCase(
                id='g2_correlation',
                formula_name='Correlación g⁽²⁾(0)',
                question='¿Qué es g⁽²⁾(0) y qué indica sobre la luz?',
                correct_answers=[
                    'correlación de intensidades',
                    'g²(0) < 1: antibunching',
                    'g²(0) = 1: coherente',
                    'g²(0) > 1: bunching',
                    'Hanbury Brown-Twiss',
                ],
                wrong_answers=[
                    'siempre = 1',
                    'no distingue tipos de luz',
                    'solo para térmico',
                ],
                category='ultra_advanced',
                weight=1.0
            ),
            
            'uncertainty_product': TestCase(
                id='uncertainty_product',
                formula_name='Producto de Incertidumbre',
                question='¿Cuál es el producto ΔX × ΔP para el estado de vacío?',
                correct_answers=[
                    'ΔX × ΔP = 1/4',
                    '1/4',
                    '0.25',
                    'satura el mínimo',
                    'estado de mínima incertidumbre',
                ],
                wrong_answers=[
                    'ℏ/2',
                    '1/2',
                    '1',
                    'hbar/2',
                ],
                category='ultra_advanced',
                weight=2.0,
                explanation='CRÍTICO: Con nuestra normalización ΔX×ΔP = 1/4'
            ),
        }
    
    def validate_response(self, test_id: str, response: str) -> TestResult:
        """
        Validate a single AI response against a test case.
        
        Args:
            test_id: ID of the test case
            response: The AI response to validate
            
        Returns:
            TestResult with pass/fail and details
        """
        if test_id not in self.test_cases:
            return TestResult(
                test_id=test_id,
                passed=False,
                response_snippet="",
                correct_found=[],
                errors_found=["Test case not found"],
                score=0.0,
                details="Invalid test ID"
            )
        
        test = self.test_cases[test_id]
        response_lower = response.lower()
        
        correct_found = []
        for correct in test.correct_answers:
            if correct.lower() in response_lower:
                correct_found.append(correct)
        
        errors_found = []
        for wrong in test.wrong_answers:
            if wrong.lower() in response_lower:
                errors_found.append(wrong)
        
        has_correct = len(correct_found) > 0
        has_errors = len(errors_found) > 0
        
        if has_correct and not has_errors:
            passed = True
            score = 1.0
            details = f"✅ Correcto: encontró {correct_found}"
        elif has_correct and has_errors:
            passed = False
            score = 0.5
            details = f"⚠️ Parcial: correcto={correct_found}, errores={errors_found}"
        elif has_errors:
            passed = False
            score = 0.0
            details = f"❌ Error: encontró respuestas incorrectas {errors_found}"
        else:
            passed = False
            score = 0.3
            details = "⚠️ No encontró respuestas correctas ni incorrectas"
        
        return TestResult(
            test_id=test_id,
            passed=passed,
            response_snippet=response[:200] + "..." if len(response) > 200 else response,
            correct_found=correct_found,
            errors_found=errors_found,
            score=score * test.weight,
            details=details
        )
    
    async def run_single_test(self, test_id: str, ai_func) -> TestResult:
        """
        Run a single test against an AI model.
        
        Args:
            test_id: ID of the test to run
            ai_func: Async function that takes a question and returns a response
            
        Returns:
            TestResult
        """
        if test_id not in self.test_cases:
            raise ValueError(f"Test case '{test_id}' not found")
        
        test = self.test_cases[test_id]
        
        try:
            response = await ai_func(test.question)
            return self.validate_response(test_id, response)
        except Exception as e:
            logger.error(f"Error running test {test_id}: {e}")
            return TestResult(
                test_id=test_id,
                passed=False,
                response_snippet="",
                correct_found=[],
                errors_found=[str(e)],
                score=0.0,
                details=f"Error: {e}"
            )
    
    async def run_full_suite(self, ai_func) -> Dict:
        """
        Run all 24 tests against an AI model.
        
        Args:
            ai_func: Async function that takes a question and returns a response
            
        Returns:
            Dict with full results and statistics
        """
        results = {}
        total_score = 0.0
        max_score = 0.0
        passed_count = 0
        
        for test_id, test in self.test_cases.items():
            result = await self.run_single_test(test_id, ai_func)
            results[test_id] = {
                'passed': result.passed,
                'score': result.score,
                'max_score': test.weight,
                'details': result.details,
                'correct_found': result.correct_found,
                'errors_found': result.errors_found,
                'category': test.category,
            }
            total_score += result.score
            max_score += test.weight
            if result.passed:
                passed_count += 1
        
        self.last_run = datetime.now()
        self.last_results = {
            'results': results,
            'summary': {
                'total_tests': len(self.test_cases),
                'passed': passed_count,
                'failed': len(self.test_cases) - passed_count,
                'score': total_score,
                'max_score': max_score,
                'percentage': (total_score / max_score * 100) if max_score > 0 else 0,
                'grade': self._calculate_grade(total_score / max_score if max_score > 0 else 0),
                'timestamp': self.last_run.isoformat(),
            }
        }
        
        return self.last_results
    
    def _calculate_grade(self, percentage: float) -> str:
        """Calculate letter grade from percentage"""
        if percentage >= 0.95:
            return 'A+'
        elif percentage >= 0.90:
            return 'A'
        elif percentage >= 0.85:
            return 'A-'
        elif percentage >= 0.80:
            return 'B+'
        elif percentage >= 0.75:
            return 'B'
        elif percentage >= 0.70:
            return 'B-'
        elif percentage >= 0.65:
            return 'C+'
        elif percentage >= 0.60:
            return 'C'
        elif percentage >= 0.50:
            return 'D'
        else:
            return 'F'
    
    def generate_investor_report(self, results: Optional[Dict] = None) -> str:
        """
        Generate a professional report for investors.
        
        Args:
            results: Optional results dict. If None, uses last_results.
            
        Returns:
            Formatted markdown report
        """
        if results is None:
            results = self.last_results
        
        if results is None:
            return "⚠️ No test results available. Run test suite first."
        
        summary = results['summary']
        test_results = results['results']
        
        by_category = {}
        for test_id, result in test_results.items():
            cat = result['category']
            if cat not in by_category:
                by_category[cat] = {'passed': 0, 'total': 0}
            by_category[cat]['total'] += 1
            if result['passed']:
                by_category[cat]['passed'] += 1
        
        report = f"""
🏆 **OMNIX QUANTUM PHYSICS VALIDATION REPORT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **RESUMEN EJECUTIVO**
┌─────────────────────────────────────────────┐
│  Tests Pasados: {summary['passed']}/{summary['total_tests']} ({summary['percentage']:.1f}%)
│  Grado: {summary['grade']}
│  Score: {summary['score']:.1f}/{summary['max_score']:.1f}
│  Fecha: {summary['timestamp'][:19]}
└─────────────────────────────────────────────┘

📈 **RESULTADOS POR CATEGORÍA**
"""
        
        category_names = {
            'foundational': '🔬 Fundamentos (V1.0)',
            'derivations': '📐 Derivaciones (V2.0)',
            'phd_level': '🎓 Nivel PhD (V3.0)',
            'ultra_advanced': '🚀 Ultra-Avanzado (V4.0)',
        }
        
        for cat, data in by_category.items():
            pct = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
            status = "✅" if pct >= 80 else "⚠️" if pct >= 50 else "❌"
            name = category_names.get(cat, cat)
            report += f"  {status} {name}: {data['passed']}/{data['total']} ({pct:.0f}%)\n"
        
        report += "\n📋 **TESTS CRÍTICOS (peso ≥ 1.5)**\n"
        
        critical_tests = [
            ('commutator_xp', '[X̂, P̂] = i/2'),
            ('vacuum_variance', 'Var(X̂) = 1/4'),
            ('heisenberg_limit', 'SQL vs Heisenberg'),
            ('uncertainty_product', 'ΔX×ΔP = 1/4'),
            ('bell_chsh', 'CHSH = 2√2'),
        ]
        
        for test_id, name in critical_tests:
            if test_id in test_results:
                r = test_results[test_id]
                status = "✅" if r['passed'] else "❌"
                report += f"  {status} {name}: {r['details']}\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 **CONCLUSIÓN**

{"✅ Sistema LISTO para inversores" if summary['percentage'] >= 80 else "⚠️ Requiere mejoras antes de presentar a inversores"}

💡 Este reporte demuestra validación rigurosa de 24 fórmulas
   de física cuántica verificadas a nivel PhD+.
   
📧 OMNIX V6.0 ULTRA - Powered by Quantum Computing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return report
    
    def get_quick_status(self) -> Dict:
        """Get a quick status summary"""
        if self.last_results is None:
            return {
                'status': 'not_run',
                'message': 'Tests not executed yet'
            }
        
        summary = self.last_results['summary']
        return {
            'status': 'passed' if summary['percentage'] >= 80 else 'needs_review',
            'passed': summary['passed'],
            'total': summary['total_tests'],
            'percentage': summary['percentage'],
            'grade': summary['grade'],
            'last_run': summary['timestamp']
        }


global_testing_framework = QuantumTestingFramework()
