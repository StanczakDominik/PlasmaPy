import numba
import math
import numpy as np


@numba.njit(parallel=True)
def _boris_push(x, v, b, e, q, m, dt):
    r"""
    Implement the explicit Boris pusher for moving and accelerating particles.

    Arguments
    ----------
    init : bool (optional)
        If `True`, does not change the particle positions and sets dt
        to -dt/2.

    Notes
    ----------
    The Boris algorithm is the standard energy conserving algorithm for
    particle movement in plasma physics. See [1]_ for more details.

    Conceptually, the algorithm has three phases:

    1. Add half the impulse from electric field.
    2. Rotate the particle velocity about the direction of the magnetic
       field.
    3. Add the second half of the impulse from the electric field.

    This ends up causing the magnetic field action to be properly
    "centered" in time, and the algorithm conserves energy.

    References
    ----------
    .. [1] C. K. Birdsall, A. B. Langdon, "Plasma Physics via Computer
           Simulation", 2004, p. 58-63
    """
    hqmdt = 0.5 * dt * q / m
    for i in numba.prange(len(x)):
        # add first half of electric impulse
        vminus = v[i] + hqmdt * e[i]

        # rotate to add magnetic field
        t = -b[i] * hqmdt
        s = 2 * t / (1 + (t[0] * t[0] + t[1] * t[1] + t[2] * t[2]))
        cross_result = np.cross(vminus, t)
        vprime = vminus + cross_result
        cross_result_2 = np.cross(vprime, s)
        vplus = vminus + cross_result_2

        # add second half of electric impulse
        v[i] = vplus + e[i] * hqmdt
        x[i] += v[i] * dt


@numba.njit(parallel=True)
def _boris_push_implicit(x, v, b, e, q, m, dt):
    r"""
    Implement the implicit Boris pusher for moving and accelerating particles.

    Arguments
    ----------
    init : bool (optional)
        If `True`, does not change the particle positions and sets dt
        to -dt/2.

    Notes
    ----------
    The Boris algorithm is the standard energy conserving algorithm for
    particle movement in plasma physics. See [1]_ for more details.

    Conceptually, the algorithm has three phases:

    1. Add half the impulse from electric field.
    2. Rotate the particle velocity about the direction of the magnetic
       field.
    3. Add the second half of the impulse from the electric field.

    This ends up causing the magnetic field action to be properly
    "centered" in time, and the algorithm conserves energy.

    References
    ----------
    .. [1] C. K. Birdsall, A. B. Langdon, "Plasma Physics via Computer
           Simulation", 2004, p. 58-63
    """
    C = q / m
    for i in numba.prange(len(x)):
        # add first half of electric impulse
        B_x, B_y, B_z = b[i]
        v_x, v_y, v_z = v[i]
        E_x, E_y, E_z = e[i]

        # calculated via sympy
        vx = (
            0.0625 * B_x ** 2 * C ** 3 * E_x * dt ** 3
            + 0.0625 * B_x ** 2 * C ** 2 * dt ** 2 * v_x
            + 0.0625 * B_x * B_y * C ** 3 * E_y * dt ** 3
            + 0.125 * B_x * B_y * C ** 2 * dt ** 2 * v_y
            + 0.0625 * B_x * B_z * C ** 3 * E_z * dt ** 3
            + 0.125 * B_x * B_z * C ** 2 * dt ** 2 * v_z
            - 0.0625 * B_y ** 2 * C ** 2 * dt ** 2 * v_x
            - 0.125 * B_y * C ** 2 * E_z * dt ** 2
            - 0.25 * B_y * C * dt * v_z
            - 0.0625 * B_z ** 2 * C ** 2 * dt ** 2 * v_x
            + 0.125 * B_z * C ** 2 * E_y * dt ** 2
            + 0.25 * B_z * C * dt * v_y
            + 0.25 * C * E_x * dt
            + 0.25 * v_x
        ) / (
            0.0625 * B_x ** 2 * C ** 2 * dt ** 2
            + 0.0625 * B_y ** 2 * C ** 2 * dt ** 2
            + 0.0625 * B_z ** 2 * C ** 2 * dt ** 2
            + 0.25
        )
        vy = (
            -0.0625 * B_x ** 2 * C ** 2 * dt ** 2 * v_y
            + 0.0625 * B_x * B_y * C ** 3 * E_x * dt ** 3
            + 0.125 * B_x * B_y * C ** 2 * dt ** 2 * v_x
            + 0.125 * B_x * C ** 2 * E_z * dt ** 2
            + 0.25 * B_x * C * dt * v_z
            + 0.0625 * B_y ** 2 * C ** 3 * E_y * dt ** 3
            + 0.0625 * B_y ** 2 * C ** 2 * dt ** 2 * v_y
            + 0.0625 * B_y * B_z * C ** 3 * E_z * dt ** 3
            + 0.125 * B_y * B_z * C ** 2 * dt ** 2 * v_z
            - 0.0625 * B_z ** 2 * C ** 2 * dt ** 2 * v_y
            - 0.125 * B_z * C ** 2 * E_x * dt ** 2
            - 0.25 * B_z * C * dt * v_x
            + 0.25 * C * E_y * dt
            + 0.25 * v_y
        ) / (
            0.0625 * B_x ** 2 * C ** 2 * dt ** 2
            + 0.0625 * B_y ** 2 * C ** 2 * dt ** 2
            + 0.0625 * B_z ** 2 * C ** 2 * dt ** 2
            + 0.25
        )
        vz = (
            -C
            * dt
            * (0.5 * B_x - 0.25 * B_y * B_z * C * dt)
            * (
                0.5 * B_x * C * dt * v_z
                - 0.5 * B_z * C * dt * v_x
                - 0.5
                * B_z
                * C
                * dt
                * (
                    -0.5 * B_y * C * dt * v_z
                    + 0.5 * B_z * C * dt * v_y
                    + C * E_x * dt
                    + v_x
                )
                + C * E_y * dt
                + v_y
            )
            + (0.25 * B_z ** 2 * C ** 2 * dt ** 2 + 1)
            * (
                -0.5 * B_x * C * dt * v_y
                + 0.5 * B_y * C * dt * v_x
                + 0.5
                * B_y
                * C
                * dt
                * (
                    -0.5 * B_y * C * dt * v_z
                    + 0.5 * B_z * C * dt * v_y
                    + C * E_x * dt
                    + v_x
                )
                + C * E_z * dt
                + v_z
            )
        ) / (
            C ** 2
            * dt ** 2
            * (0.5 * B_x - 0.25 * B_y * B_z * C * dt)
            * (0.5 * B_x + 0.25 * B_y * B_z * C * dt)
            + (0.25 * B_y ** 2 * C ** 2 * dt ** 2 + 1)
            * (0.25 * B_z ** 2 * C ** 2 * dt ** 2 + 1)
        )
        v[i] = (vx, vy, vz)
        x[i] += v[i] * dt


@numba.njit(parallel=True)
def _boris_push_implicit2(x, v, b, e, q, m, dt):
    r"""
    Implement the implicit Boris pusher for moving and accelerating particles.
    DOES NOT HANDLE ELECTRIC FIELDS RIGHT NOW

    Arguments
    ----------
    init : bool (optional)
        If `True`, does not change the particle positions and sets dt
        to -dt/2.

    Notes
    ----------
    The Boris algorithm is the standard energy conserving algorithm for
    particle movement in plasma physics. See [1]_ for more details.

    Conceptually, the algorithm has three phases:

    1. Add half the impulse from electric field.
    2. Rotate the particle velocity about the direction of the magnetic
       field.
    3. Add the second half of the impulse from the electric field.

    This ends up causing the magnetic field action to be properly
    "centered" in time, and the algorithm conserves energy.

    References
    ----------
    .. [1] C. K. Birdsall, A. B. Langdon, "Plasma Physics via Computer
           Simulation", 2004, p. 58-63
    """
    C = q / m * dt
    for i in numba.prange(len(x)):
        # add first half of electric impulse
        B_i, B_j, B_k = b[i]
        v_i, v_j, v_k = v[i]
        E_x, E_y, E_z = e[i]
        vx = (
            2
            * C
            * v_j
            * (B_i * B_j * C + 2 * B_k)
            / (B_i ** 2 * C ** 2 + B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
            + 2
            * C
            * v_k
            * (B_i * B_k * C - 2 * B_j)
            / (B_i ** 2 * C ** 2 + B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
            + v_i
            * (B_i ** 2 * C ** 2 - B_j ** 2 * C ** 2 - B_k ** 2 * C ** 2 + 4)
            / (B_i ** 2 * C ** 2 + B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
        )
        vy = (
            2
            * C
            * v_i
            * (B_i * B_j * C - 2 * B_k)
            / (B_i ** 2 * C ** 2 + B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
            + 2
            * C
            * v_k
            * (2 * B_i + B_j * B_k * C)
            / (B_i ** 2 * C ** 2 + B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
            + v_j
            * (-(B_i ** 2) * C ** 2 + B_j ** 2 * C ** 2 - B_k ** 2 * C ** 2 + 4)
            / (B_i ** 2 * C ** 2 + B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
        )
        vz = (
            2
            * C
            * v_i
            * (B_i * B_k * C + 2 * B_j)
            / (B_i ** 2 * C ** 2 + B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
            - 2
            * C
            * v_j
            * (2 * B_i - B_j * B_k * C)
            / (B_i ** 2 * C ** 2 + B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
            + v_k
            * (-(B_i ** 2) * C ** 2 - B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
            / (B_i ** 2 * C ** 2 + B_j ** 2 * C ** 2 + B_k ** 2 * C ** 2 + 4)
        )
        v[i] = (vx, vy, vz)
        x[i] += v[i] * dt


from astropy import constants

c = constants.c.si.value


@numba.njit()
def gamma_from_velocity(velocity):
    return np.sqrt(1 - ((np.linalg.norm(velocity) / c) ** 2))


@numba.njit()
def gamma_from_u(u):
    return np.sqrt(1 + ((np.linalg.norm(u) / c) ** 2))


@numba.njit(parallel=True)
def _zenitani(x, v, b, e, q, m, dt, B_numerical_threshold=1e-20):
    r"""
    Implement the Zenitani-Umeda pusher

    Arguments
    ----------
    TODO

    Notes
    ----------
    TODO

    References
    ----------
    .. [1] Seiji Zenitani and Takayuki Umeda,
           On the Boris solver in particle-in-cell simulation
           Physics of Plasmas 25, 112110 (2018); https://doi.org/10.1063/1.5051077
    """
    C = q / m * dt
    for i in numba.prange(len(x)):
        # add first half of electric impulse
        epsilon = C / 2.0 * e[i]
        uminus = v[i] + epsilon
        magfield_norm = max((np.linalg.norm(b[i]), B_numerical_threshold))
        theta = C * magfield_norm / gamma_from_u(uminus)  # Eq. 6
        bnormed = b[i] / magfield_norm
        u_parallel_minus = np.dot(uminus, bnormed) * bnormed  # Eq. 11
        uplus = (
            u_parallel_minus
            + (uminus - u_parallel_minus) * math.cos(theta)
            + np.cross(uminus, bnormed) * math.sin(theta)
        )  # Eq. 12
        u_t_plus_half = uplus + epsilon
        v[i] = u_t_plus_half / gamma_from_u(u_t_plus_half)
        x[i] += v[i] * dt