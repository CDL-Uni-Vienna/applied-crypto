from IPython.display import display, HTML
display(HTML("<style>.container { width:100% !important; }</style>"))
from abc import ABC

import numpy as np
# Importing standard Qiskit libraries
from qiskit import QuantumCircuit, transpile, Aer, IBMQ, execute
from qiskit.tools.jupyter import *
from qiskit.visualization import *

from qiskit.algorithms import *

def run(circuit):
    job = execute(circuit, backend, shots = 1024)
    r = job.result().get_counts()
    return r

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Shor's factoring algorithm."""

from typing import Optional, Union, Tuple, List
import math
import array
import fractions
import logging as logger
import numpy as np

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import Gate, Instruction, ParameterVector
from qiskit.circuit.library import QFT

from qiskit.providers import Backend

from qiskit.utils import QuantumInstance
from qiskit.utils import summarize_circuits
from qiskit.utils.arithmetic import is_power
from qiskit_algorithms.utils.validation import validate_min


class MyShor(ABC):
    """Shor's factoring algorithm.

    Shor's Factoring algorithm is one of the most well-known quantum algorithms and finds the
    prime factors for input integer :math:`N` in polynomial time.

    The input integer :math:`N` to be factored is expected to be odd and greater than 2.
    Even though this implementation is general, its capability will be limited by the
    capacity of the simulator/hardware. Another input integer :math:`a`  can also be supplied,
    which needs to be a co-prime smaller than :math:`N` .
    """

    def __init__(self,
                 N: int = 15,
                 a: int = 2,
                 quantum_instance: Optional[
                     Union[QuantumInstance, Backend]] = None) -> None:
        """
        Args:
            N: The integer to be factored, has a min. value of 3.
            a: Any integer that satisfies 1 < a < N and gcd(a, N) = 1.
            quantum_instance: Quantum Instance or Backend

         Raises:
            ValueError: Invalid input
        """
        validate_min('N', N, 3)
        validate_min('a', a, 2)
        #super().__init__(quantum_instance)
        self._n = None  # type: Optional[int]
        self._up_qreg = None
        self._down_qreg = None  # type: Optional[QuantumRegister]
        self._aux_qreg = None  # type: Optional[QuantumRegister]

        # check the input integer
        if N < 1 or N % 2 == 0:
            raise ValueError('The input needs to be an odd integer greater than 1.')

        self._N = N

        if a >= N or math.gcd(a, self._N) != 1:
            raise ValueError('The integer a needs to satisfy a < N and gcd(a, N) = 1.')

        self._a = a

        #self._ret = AlgorithmResult({"factors": [], "total_counts": 0, "successful_counts": 0})
        self._ret = {"factors": [], "total_counts": 0, "successful_counts": 0}

        # check if the input integer is a power
        tf, b, p = is_power(N, return_decomposition=True)
        if tf:
            logger.info('The input integer is a power: %s=%s^%s.', N, b, p)
            self._ret['factors'].append(b)

        self._qft = QFT(do_swaps=False).to_instruction()
        self._iqft = self._qft.inverse()

        self._phi_add_N = None  # type: Optional[Gate]
        self._iphi_add_N = None

    def _get_angles(self, a: int) -> np.ndarray:
        """Calculates the array of angles to be used in the addition in Fourier Space."""
        s = bin(int(a))[2:].zfill(self._n + 1)
        angles = np.zeros([self._n + 1])
        for i in range(0, self._n + 1):
            for j in range(i, self._n + 1):
                if s[j] == '1':
                    angles[self._n - i] += math.pow(2, -(j - i))
            angles[self._n - i] *= np.pi
        return angles[::-1]

    @staticmethod
    def _phi_add_gate(size: int, angles: Union[np.ndarray, ParameterVector]) -> Gate:
        """Gate that performs addition by a in Fourier Space."""
        circuit = QuantumCircuit(size, name="phi_add")
        for i, angle in enumerate(angles):
            circuit.p(angle, i)
        return circuit.to_gate()

    def _double_controlled_phi_add_mod_N(self,
                                         num_qubits: int,
                                         angles: Union[np.ndarray, ParameterVector]
                                         ) -> QuantumCircuit:
        """Creates a circuit which implements double-controlled modular addition by a."""
        circuit = QuantumCircuit(num_qubits, name="phi_add")

        ctl_up = 0
        ctl_down = 1
        ctl_aux = 2

        # get qubits from aux register, omitting the control qubit
        qubits = range(3, num_qubits)
        
        qft = QFT(len(qubits)).to_instruction()
        iqft = qft.inverse()

        # store the gates representing addition/subtraction by a in Fourier Space
        phi_add_a = self._phi_add_gate(len(qubits), angles)
        iphi_add_a = phi_add_a.inverse()

        circuit.append(phi_add_a.control(2), [ctl_up, ctl_down, *qubits])
        circuit.append(self._iphi_add_N, qubits)
        circuit.append(iqft, qubits)

        circuit.cx(qubits[0], ctl_aux)

        circuit.append(qft, qubits)
        circuit.append(self._phi_add_N, qubits)
        circuit.append(iphi_add_a.control(2), [ctl_up, ctl_down, *qubits])
        circuit.append(iqft, qubits)

        circuit.x(qubits[0])
        circuit.cx(qubits[0], ctl_aux)
        circuit.x(qubits[0])

        circuit.append(qft, qubits)
        circuit.append(phi_add_a.control(2), [ctl_up, ctl_down, *qubits])
        
        return circuit

    def _controlled_multiple_mod_N(self, num_qubits: int, a: int) -> Instruction:
        """Implements modular multiplication by a as an instruction."""
        circuit = QuantumCircuit(
            num_qubits, name="multiply_by_{}_mod_{}".format(a % self._N, self._N)
        )
        down = circuit.qubits[1: self._n + 1]
        aux = circuit.qubits[self._n + 1:]
        qubits = [aux[i] for i in reversed(range(self._n + 1))]
        ctl_up = 0
        ctl_aux = aux[-1]

        angle_params = ParameterVector("angles", length=len(aux) - 1)
        double_controlled_phi_add = self._double_controlled_phi_add_mod_N(
            len(aux) + 2, angle_params
        )
        idouble_controlled_phi_add = double_controlled_phi_add.inverse()
        
        qft = QFT(len(qubits)).to_instruction()
        iqft = qft.inverse()
        
        circuit.append(qft, qubits)

        # perform controlled addition by a on the aux register in Fourier space
        for i, ctl_down in enumerate(down):
            a_exp = (2 ** i) * a % self._N
            angles = self._get_angles(a_exp)
            bound = double_controlled_phi_add.assign_parameters({angle_params: angles})
            circuit.append(bound, [ctl_up, ctl_down, ctl_aux, *qubits])

        circuit.append(iqft, qubits)

        # perform controlled subtraction by a in Fourier space on both the aux and down register
        for j in range(self._n):
            circuit.cswap(ctl_up, down[j], aux[j])
        circuit.append(qft, qubits)

        a_inv = self.modinv(a, self._N)
        for i in reversed(range(len(down))):
            a_exp = (2 ** i) * a_inv % self._N
            angles = self._get_angles(a_exp)
            bound = idouble_controlled_phi_add.assign_parameters({angle_params: angles})
            circuit.append(bound, [ctl_up, down[i], ctl_aux, *qubits])

        circuit.append(iqft, qubits)
        #print(circuit)
        return circuit.to_instruction()

    def construct_circuit(self, measurement: bool = False) -> QuantumCircuit:
        """Construct circuit.

        Args:
            measurement: Boolean flag to indicate if measurement should be included in the circuit.

        Returns:
            Quantum circuit.
        """

        # Get n value used in Shor's algorithm, to know how many qubits are used
        self._n = math.ceil(math.log(self._N, 2))
        self._qft.num_qubits = self._n + 1
        self._iqft.num_qubits = self._n + 1

        # quantum register where the sequential QFT is performed
        self._up_qreg = QuantumRegister(2 * self._n, name='up')
        # quantum register where the multiplications are made
        self._down_qreg = QuantumRegister(self._n, name='down')
        # auxiliary quantum register used in addition and multiplication
        self._aux_qreg = QuantumRegister(self._n + 2, name='aux')

        # Create Quantum Circuit
        circuit = QuantumCircuit(self._up_qreg,
                                 self._down_qreg,
                                 self._aux_qreg,
                                 name="Shor(N={}, a={})".format(self._N, self._a))

        # Create gates to perform addition/subtraction by N in Fourier Space
        self._phi_add_N = self._phi_add_gate(self._aux_qreg.size - 1, self._get_angles(self._N))
        self._iphi_add_N = self._phi_add_N.inverse()

        # Create maximal superposition in top register
        circuit.h(self._up_qreg)

        # Initialize down register to 1
        circuit.x(self._down_qreg[0])

        # Apply the multiplication gates as showed in
        # the report in order to create the exponentiation
        for i, ctl_up in enumerate(self._up_qreg):  # type: ignore
            a = int(pow(self._a, pow(2, i)))
            controlled_multiple_mod_N = self._controlled_multiple_mod_N(
                len(self._down_qreg) + len(self._aux_qreg) + 1, a,
            )
            circuit.append(
                controlled_multiple_mod_N, [ctl_up, *self._down_qreg, *self._aux_qreg]
            )
        
        # Apply inverse QFT
        iqft = QFT(len(self._up_qreg)).inverse().reverse_bits().to_instruction()
        circuit.append(iqft, self._up_qreg)

        if measurement:
            up_cqreg = ClassicalRegister(2 * self._n, name='m')
            circuit.add_register(up_cqreg)
            circuit.measure(self._up_qreg, up_cqreg)

        logger.info(summarize_circuits(circuit))

        return circuit

    @staticmethod
    def modinv(a: int, m: int) -> int:
        """Returns the modular multiplicative inverse of a with respect to the modulus m."""
        def egcd(a: int, b: int) -> Tuple[int, int, int]:
            if a == 0:
                return b, 0, 1
            else:
                g, y, x = egcd(b % a, a)
                return g, x - (b // a) * y, y

        g, x, _ = egcd(a, m)
        if g != 1:
            raise ValueError("The greatest common divisor of {} and {} is {}, so the "
                             "modular inverse does not exist.".format(a, m, g))
        return x % m

    def get_period(self, keylist: list):
        period = []
        for measurement in keylist:
            """Apply the continued fractions to find r and the gcd to find the desired factors."""
            x_final = int(measurement, 2)
            logger.info('In decimal, x_final value for this result is: %s.', x_final)

            if x_final <= 0:
                fail_reason = 'x_final value is <= 0, there are no continued fractions.'
            else:
                fail_reason = None
                logger.debug('Running continued fractions for this case.')

            # Calculate T and x/T
            T_upper = len(measurement)
            T = pow(2, T_upper)
            x_over_T = x_final / T

            # Cycle in which each iteration corresponds to putting one more term in the
            # calculation of the Continued Fraction (CF) of x/T

            # Initialize the first values according to CF rule
            i = 0
            b = array.array('i')
            t = array.array('f')

            b.append(math.floor(x_over_T))
            t.append(x_over_T - b[i])

            exponential = 0.0
                
            
            while i < self._N and fail_reason is None:
                # From the 2nd iteration onwards, calculate the new terms of the CF based
                # on the previous terms as the rule suggests
                if i > 0:
                    b.append(math.floor(1 / t[i - 1]))
                    t.append((1 / t[i - 1]) - b[i])  # type: ignore

                # Calculate the denominator of the CF using the known terms
                denominator = self._calculate_continued_fraction(b)

                # Increment i for next iteration
                i += 1

                if denominator < 1000:
                    try:
                        exponential = pow(self._a, denominator / 2)
                    except OverflowError:
                        pass

                # Check if the value is too big or not
                if exponential > 1000000000:
                    fail_reason = 'denominator of continued fraction is too big.'
                if pow(self._a, denominator, self._N) == 1: 
                    period.append(denominator)
                if t[len(t)-1] == 0:
                    break
        return min(period)
        

    @staticmethod
    def _calculate_continued_fraction(b: array.array) -> int:
        """Calculate the continued fraction of x/T from the current terms of expansion b."""

        x_over_T = 0

        for i in reversed(range(len(b) - 1)):
            x_over_T = 1 / (b[i + 1] + x_over_T)

        x_over_T += b[0]

        # Get the denominator from the value obtained
        frac = fractions.Fraction(x_over_T).limit_denominator()

        logger.debug('Approximation number %s of continued fractions:', len(b))
        logger.debug("Numerator:%s \t\t Denominator: %s.", frac.numerator, frac.denominator)
        return frac.denominator
    
    def _run(self):
        return 0