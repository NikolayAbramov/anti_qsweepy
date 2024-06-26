"""
Copyright (c) 2005-2022, NumPy Developers.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above
       copyright notice, this list of conditions and the following
       disclaimer in the documentation and/or other materials provided
       with the distribution.

    * Neither the name of the NumPy Developers nor the names of any
       contributors may be used to endorse or promote products derived
       from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

"""
Modified version of differential evolution global optimization algorithm from Numpy
"""
import warnings
import numpy as np
from scipy.optimize import OptimizeResult, minimize
from scipy.optimize._constraints import (Bounds, new_bounds_to_old,
                                         NonlinearConstraint, LinearConstraint)
from scipy.sparse import issparse

__all__ = ['differential_evolution']
_MACHEPS = np.finfo(np.float64).eps


def differential_evolution(func, bounds, args=(), strategy='best1bin',
                           maxiter=1000, maxiter_conv=10, threshold=150,
                           popsize=15, minpopsize=10, tol=0.01, std_conv=1,
                           mutation=(0.5, 1), recombination=0.7, seed=None,
                           callback=None, disp=False, polish=True,
                           init='latinhypercube', atol=0,
                           constraints=(), x0=None, *,
                           integrality=None):
    """Finds the global minimum of a multivariate function.
    Differential Evolution is stochastic in nature (does not use gradient
    methods) to find the minimum, and can search large areas of candidate
    space, but often requires larger numbers of function evaluations than
    conventional gradient-based techniques.
    The algorithm is due to Storn and Price [1]_.
    Parameters
    ----------
    func : callable
        The objective function to be minimized. Must be in the form
        ``f(x, *args)``, where ``x`` is the argument in the form of a 1-D array
        and ``args`` is a  tuple of any additional fixed parameters needed to
        completely specify the function.
    bounds : sequence or `Bounds`
        Bounds for variables. There are two ways to specify the bounds:
        1. Instance of `Bounds` class.
        2. ``(min, max)`` pairs for each element in ``x``, defining the finite
        lower and upper bounds for the optimizing argument of `func`. It is
        required to have ``len(bounds) == len(x)``. ``len(bounds)`` is used
        to determine the number of parameters in ``x``.
    args : tuple, optional
        Any additional fixed parameters needed to
        completely specify the objective function.
    strategy : str, optional
        The differential evolution strategy to use. Should be one of:
            - 'best1bin'
            - 'best1exp'
            - 'rand1exp'
            - 'randtobest1exp'
            - 'currenttobest1exp'
            - 'best2exp'
            - 'rand2exp'
            - 'randtobest1bin'
            - 'currenttobest1bin'
            - 'best2bin'
            - 'rand2bin'
            - 'rand1bin'
        The default is 'best1bin'.
    maxiter : int, optional
        The maximum number of generations over which the entire population is
        evolved. The maximum number of function evaluations (with no polishing)
        is: ``(maxiter + 1) * popsize * len(x)``
    popsize : int, optional
        A multiplier for setting the total population size. The population has
        ``popsize * len(x)`` individuals. This keyword is overridden if an
        initial population is supplied via the `init` keyword. When using
        ``init='sobol'`` the population size is calculated as the next power
        of 2 after ``popsize * len(x)``.
    tol : float, optional
        Relative tolerance for convergence, the solving stops when
        ``np.std(pop) <= atol + tol * np.abs(np.mean(population_energies))``,
        where and `atol` and `tol` are the absolute and relative tolerance
        respectively.
    mutation : float or tuple(float, float), optional
        The mutation constant. In the literature this is also known as
        differential weight, being denoted by F.
        If specified as a float it should be in the range [0, 2].
        If specified as a tuple ``(min, max)`` dithering is employed. Dithering
        randomly changes the mutation constant on a generation by generation
        basis. The mutation constant for that generation is taken from
        ``U[min, max)``. Dithering can help speed convergence significantly.
        Increasing the mutation constant increases the search radius, but will
        slow down convergence.
    recombination : float, optional
        The recombination constant, should be in the range [0, 1]. In the
        literature this is also known as the crossover probability, being
        denoted by CR. Increasing this value allows a larger number of mutants
        to progress into the next generation, but at the risk of population
        stability.
    seed : {None, int, `numpy.random.Generator`,
            `numpy.random.RandomState`}, optional
        If `seed` is None (or `np.random`), the `numpy.random.RandomState`
        singleton is used.
        If `seed` is an int, a new ``RandomState`` instance is used,
        seeded with `seed`.
        If `seed` is already a ``Generator`` or ``RandomState`` instance then
        that instance is used.
        Specify `seed` for repeatable minimizations.
    disp : bool, optional
        Prints the evaluated `func` at every iteration.
    callback : callable, `callback(xk, convergence=val)`, optional
        A function to follow the progress of the minimization. ``xk`` is
        the best solution found so far. ``val`` represents the fractional
        value of the population convergence.  When ``val`` is greater than one
        the function halts. If callback returns `True`, then the minimization
        is halted (any polishing is still carried out).
    polish : bool, optional
        If True (default), then `scipy.optimize.minimize` with the `L-BFGS-B`
        method is used to polish the best population member at the end, which
        can improve the minimization slightly. If a constrained problem is
        being studied then the `trust-constr` method is used instead.
    init : str or array-like, optional
        Specify which type of population initialization is performed. Should be
        one of:
            - 'latinhypercube'
            - 'sobol'
            - 'halton'
            - 'random'
            - array specifying the initial population. The array should have
              shape ``(M, len(x))``, where M is the total population size and
              len(x) is the number of parameters.
              `init` is clipped to `bounds` before use.
        The default is 'latinhypercube'. Latin Hypercube sampling tries to
        maximize coverage of the available parameter space.
        'sobol' and 'halton' are superior alternatives and maximize even more
        the parameter space. 'sobol' will enforce an initial population
        size which is calculated as the next power of 2 after
        ``popsize * len(x)``. 'halton' has no requirements but is a bit less
        efficient. See `scipy.stats.qmc` for more details.
        'random' initializes the population randomly - this has the drawback
        that clustering can occur, preventing the whole of parameter space
        being covered. Use of an array to specify a population could be used,
        for example, to create a tight bunch of initial guesses in an location
        where the solution is known to exist, thereby reducing time for
        convergence.
    atol : float, optional
        Absolute tolerance for convergence, the solving stops when
        ``np.std(pop) <= atol + tol * np.abs(np.mean(population_energies))``,
        where and `atol` and `tol` are the absolute and relative tolerance
        respectively.
    constraints : {NonLinearConstraint, LinearConstraint, Bounds}
        Constraints on the solver, over and above those applied by the `bounds`
        kwd. Uses the approach by Lampinen [5]_.
        .. versionadded:: 1.4.0
    x0 : None or array-like, optional
        Provides an initial guess to the minimization. Once the population has
        been initialized this vector replaces the first (best) member. This
        replacement is done even if `init` is given an initial population.
        .. versionadded:: 1.7.0
    integrality : 1-D array, optional
        For each decision variable, a boolean value indicating whether the
        decision variable is constrained to integer values. The array is
        broadcast to ``(len(x),)``.
        If any decision variables are constrained to be integral, they will not
        be changed during polishing.
        Only integer values lying between the lower and upper bounds are used.
        If there are no integer values lying between the bounds then a
        `ValueError` is raised.
        .. versionadded:: 1.9.0
    Returns
    -------
    res : OptimizeResult
        The optimization result represented as a `OptimizeResult` object.
        Important attributes are: ``x`` the solution array, ``success`` a
        Boolean flag indicating if the optimizer exited successfully and
        ``message`` which describes the cause of the termination. See
        `OptimizeResult` for a description of other attributes. If `polish`
        was employed, and a lower minimum was obtained by the polishing, then
        OptimizeResult also contains the ``jac`` attribute.
        If the eventual solution does not satisfy the applied constraints
        ``success`` will be `False`.
    """

    # using a context manager means that any created Pool objects are
    # cleared up.
    with DifferentialEvolutionSolver(func, bounds, args=args,
                                     strategy=strategy,
                                     maxiter=maxiter,
                                     maxiter_conv=maxiter_conv,
                                     threshold=threshold,
                                     popsize=popsize, minpopsize=minpopsize,
                                     tol=tol,
                                     std_conv=std_conv,
                                     mutation=mutation,
                                     recombination=recombination,
                                     seed=seed, polish=polish,
                                     callback=callback,
                                     disp=disp, init=init, atol=atol,
                                     constraints=constraints,
                                     x0=x0,
                                     integrality=integrality) as solver:
        ret = solver.solve()

    return ret


class AbortException(Exception):
    pass


class DifferentialEvolutionSolver:
    # Dispatch of mutation strategy method (binomial or exponential).
    _binomial = {'best1bin': '_best1',
                 'randtobest1bin': '_randtobest1',
                 'currenttobest1bin': '_currenttobest1',
                 'best2bin': '_best2',
                 'rand2bin': '_rand2',
                 'rand1bin': '_rand1'}
    _exponential = {'best1exp': '_best1',
                    'rand1exp': '_rand1',
                    'randtobest1exp': '_randtobest1',
                    'currenttobest1exp': '_currenttobest1',
                    'best2exp': '_best2',
                    'rand2exp': '_rand2'}

    __init_error_msg = ("The population initialization method must be one of "
                        "'latinhypercube' or 'random', or an array of shape "
                        "(M, N) where N is the number of parameters and M>5")

    def __init__(self, func,
                       bounds,
                       args=(),
                       strategy='best1bin',
                       maxiter=1000,
                       maxiter_conv=10,
                       threshold=150,
                       popsize=15,
                       minpopsize=10,
                       tol=0.01,
                       std_conv=1,
                       mutation=(0.5, 1),
                       recombination=0.7,
                       seed=None,
                       maxfun=np.inf,
                       callback=None,
                       disp=False,
                       polish=True,
                       init='latinhypercube',
                       atol=0,
                       constraints=(),
                       x0=None,
                       integrality=None):
        if strategy in self._binomial:
            self.mutation_func = getattr(self, self._binomial[strategy])
        elif strategy in self._exponential:
            self.mutation_func = getattr(self, self._exponential[strategy])
        else:
            raise ValueError("Please select a valid mutation strategy")
        self.strategy = strategy

        self.callback = callback
        self.polish = polish

        # relative and absolute tolerances for convergence
        self.tol, self.atol = tol, atol

        # Mutation constant should be in [0, 2). If specified as a sequence
        # then dithering is performed.
        self.scale = mutation
        if (not np.all(np.isfinite(mutation)) or
                np.any(np.array(mutation) >= 2) or
                np.any(np.array(mutation) < 0)):
            raise ValueError('The mutation constant must be a float in '
                             'U[0, 2), or specified as a tuple(min, max)'
                             ' where min < max and min, max are in U[0, 2).')

        self.dither = None
        if hasattr(mutation, '__iter__') and len(mutation) > 1:
            self.dither = [mutation[0], mutation[1]]
            self.dither.sort()

        self.cross_over_probability = recombination
        self.func = func
        self.args = args

        # convert tuple of lower and upper bounds to limits
        # [(low_0, high_0), ..., (low_n, high_n]
        #	 -> [[low_0, ..., low_n], [high_0, ..., high_n]]
        if isinstance(bounds, Bounds):
            self.limits = np.array(new_bounds_to_old(bounds.lb,
                                                     bounds.ub,
                                                     len(bounds.lb)),
                                   dtype=float).T
        else:
            self.limits = np.array(bounds, dtype='float').T

        if (np.size(self.limits, 0) != 2 or not
        np.all(np.isfinite(self.limits))):
            raise ValueError('bounds should be a sequence containing '
                             'real valued (min, max) pairs for each value'
                             ' in x')

        if maxiter is None:  # the default used to be None
            maxiter = 1000
        self.maxiter = maxiter
        if maxfun is None:  # the default used to be None
            maxfun = np.inf
        self.maxfun = maxfun
        self.maxiter_conv = maxiter_conv

        # population is scaled to between [0, 1].
        # We have to scale between parameter <-> population
        # save these arguments for _scale_parameter and
        # _unscale_parameter. This is an optimization
        self.__scale_arg1 = 0.5 * (self.limits[0] + self.limits[1])
        self.__scale_arg2 = np.fabs(self.limits[0] - self.limits[1])

        self.parameter_count = np.size(self.limits, 1)

        self.random_number_generator = np.random.RandomState(seed)

        # Which parameters are going to be integers?
        if np.any(integrality):
            # # user has provided a truth value for integer constraints
            integrality = np.broadcast_to(
                integrality,
                self.parameter_count
            )
            integrality = np.asarray(integrality, bool)
            # For integrality parameters change the limits to only allow
            # integer values lying between the limits.
            lb, ub = np.copy(self.limits)

            lb = np.ceil(lb)
            ub = np.floor(ub)
            if not (lb[integrality] <= ub[integrality]).all():
                # there's a parameter that doesn't have an integer value
                # lying between the limits
                raise ValueError("One of the integrality constraints does not"
                                 " have any possible integer values between"
                                 " the lower/upper bounds.")
            nlb = np.nextafter(lb[integrality] - 0.5, np.inf)
            nub = np.nextafter(ub[integrality] + 0.5, -np.inf)

            self.integrality = integrality
            self.limits[0, self.integrality] = nlb
            self.limits[1, self.integrality] = nub
        else:
            self.integrality = False

        # default population initialization is a latin hypercube design, but
        # there are other population initializations possible.
        # the minimum is 5 because 'best2bin' requires a population that's at
        # least 5 long
        self.min_pop_membes = minpopsize * self.parameter_count
        self.num_population_members = max(popsize * self.parameter_count, self.min_pop_membes)

        if (self.num_population_members < 5):
            raise ValueError('Population size is too small!')
        self.population_shape = (self.num_population_members,
                                 self.parameter_count)

        self._nfev = 0
        # check first str otherwise will fail to compare str with array
        if isinstance(init, str):
            if init == 'latinhypercube':
                self.init_population_lhs()
            elif init == 'sobol':
                # must be Ns = 2**m for Sobol'
                n_s = int(2 ** np.ceil(np.log2(self.num_population_members)))
                self.num_population_members = n_s
                self.population_shape = (self.num_population_members,
                                         self.parameter_count)
                self.init_population_qmc(qmc_engine='sobol')
            elif init == 'halton':
                self.init_population_qmc(qmc_engine='halton')
            elif init == 'random':
                self.init_population_random()
            else:
                raise ValueError(self.__init_error_msg)
        else:
            self.init_population_array(init)

        self.population_density = self.num_population_members / self._calculate_population_volume()

        if x0 is not None:
            # scale to within unit interval and
            # ensure parameters are within bounds.
            x0_scaled = self._unscale_parameters(np.asarray(x0))
            if ((x0_scaled > 1.0) | (x0_scaled < 0.0)).any():
                raise ValueError(
                    "Some entries in x0 lay outside the specified bounds"
                )
            self.population[0] = x0_scaled

        # infrastructure for constraints
        self.constraints = constraints
        self._wrapped_constraints = []

        if hasattr(constraints, '__len__'):
            # sequence of constraints, this will also deal with default
            # keyword parameter
            for c in constraints:
                self._wrapped_constraints.append(
                    _ConstraintWrapper(c, self.x)
                )
        else:
            self._wrapped_constraints = [
                _ConstraintWrapper(constraints, self.x)
            ]

        self.constraint_violation = np.zeros((self.num_population_members, 1))
        self.feasible = np.ones(self.num_population_members, bool)

        self.disp = disp
        self.threshold = threshold

        self.improved = False
        self.best_energy = None
        self.std_conv = std_conv
        # Flag for aborting thread
        self._abort = False

    def abort(self) -> None:
        """Abort for solve()
        method executing as a separate thread"""
        self._abort = True

    def init_population_lhs(self):
        """
        Initializes the population with Latin Hypercube Sampling.
        Latin Hypercube Sampling ensures that each parameter is uniformly
        sampled over its range.
        """
        rng = self.random_number_generator

        # Each parameter range needs to be sampled uniformly. The scaled
        # parameter range ([0, 1)) needs to be split into
        # `self.num_population_members` segments, each of which has the following
        # size:
        segsize = 1.0 / self.num_population_members

        # Within each segment we sample from a uniform random distribution.
        # We need to do this sampling for each parameter.
        samples = (segsize * rng.uniform(size=self.population_shape)

                   # Offset each segment to cover the entire parameter range [0, 1)
                   + np.linspace(0., 1., self.num_population_members,
                                 endpoint=False)[:, np.newaxis])

        # Create an array for population of candidate solutions.
        self.population = np.zeros_like(samples)

        # Initialize population of candidate solutions by permutation of the
        # random samples.
        for j in range(self.parameter_count):
            order = rng.permutation(range(self.num_population_members))
            self.population[:, j] = samples[order, j]

        # reset population energies
        self.population_energies = np.full(self.num_population_members,
                                           np.inf)

        # reset number of function evaluations counter
        self._nfev = 0

    def init_population_qmc(self, qmc_engine):
        """Initializes the population with a QMC method.
        QMC methods ensures that each parameter is uniformly
        sampled over its range.
        Parameters
        ----------
        qmc_engine : str
            The QMC method to use for initialization. Can be one of
            ``latinhypercube``, ``sobol`` or ``halton``.
        """
        from scipy.stats import qmc

        rng = self.random_number_generator

        # Create an array for population of candidate solutions.
        if qmc_engine == 'latinhypercube':
            sampler = qmc.LatinHypercube(d=self.parameter_count, seed=rng)
        elif qmc_engine == 'sobol':
            sampler = qmc.Sobol(d=self.parameter_count, seed=rng)
        elif qmc_engine == 'halton':
            sampler = qmc.Halton(d=self.parameter_count, seed=rng)
        else:
            raise ValueError(self.__init_error_msg)

        self.population = sampler.random(n=self.num_population_members)

        # reset population energies
        self.population_energies = np.full(self.num_population_members,
                                           np.inf)

        # reset number of function evaluations counter
        self._nfev = 0

    def init_population_random(self):
        """
        Initializes the population at random. This type of initialization
        can possess clustering, Latin Hypercube sampling is generally better.
        """
        rng = self.random_number_generator
        self.population = rng.uniform(size=self.population_shape)

        # reset population energies
        self.population_energies = np.full(self.num_population_members,
                                           np.inf)

        # reset number of function evaluations counter
        self._nfev = 0

    def init_population_array(self, init):
        """
        Initializes the population with a user specified population.
        Parameters
        ----------
        init : np.ndarray
            Array specifying subset of the initial population. The array should
            have shape (M, len(x)), where len(x) is the number of parameters.
            The population is clipped to the lower and upper bounds.
        """
        # make sure you're using a float array
        popn = np.asfarray(init)

        if (np.size(popn, 0) < 5 or
                popn.shape[1] != self.parameter_count or
                len(popn.shape) != 2):
            raise ValueError("The population supplied needs to have shape"
                             " (M, len(x)), where M > 4.")

        # scale values and clip to bounds, assigning to population
        self.population = np.clip(self._unscale_parameters(popn), 0, 1)

        self.num_population_members = np.size(self.population, 0)

        self.population_shape = (self.num_population_members,
                                 self.parameter_count)

        # reset population energies
        self.population_energies = np.full(self.num_population_members,
                                           np.inf)

        # reset number of function evaluations counter
        self._nfev = 0

    @property
    def x(self):
        """
        The best solution from the solver
        """
        return self._scale_parameters(self.population[0])

    @property
    def convergence(self):
        """
        The standard deviation of the population energies divided by their
        mean.
        """
        if np.any(np.isinf(self.population_energies)):
            return np.inf
        return (np.std(self.population_energies) /
                np.abs(np.mean(self.population_energies) + _MACHEPS))

    def converged(self):
        """
        Return True if the solver has converged.
        """
        if np.any(np.isinf(self.population_energies)):
            return False

        return (np.std(self.population_energies) <=
                self.atol +
                self.tol * np.abs(np.mean(self.population_energies)))

    def solve(self):
        """
        Runs the DifferentialEvolutionSolver.
        Returns
        -------
        res : OptimizeResult
            The optimization result represented as a ``OptimizeResult`` object.
            Important attributes are: ``x`` the solution array, ``success`` a
            Boolean flag indicating if the optimizer exited successfully and
            ``message`` which describes the cause of the termination. See
            `OptimizeResult` for a description of other attributes.  If `polish`
            was employed, and a lower minimum was obtained by the polishing,
            then OptimizeResult also contains the ``jac`` attribute.
        """
        nit, warning_flag = 0, False
        status_message = 'Optimization terminated successfully.'

        # The population may have just been initialized (all entries are
        # np.inf). If it has you have to calculate the initial energies.
        # Although this is also done in the evolve generator it's possible
        # that someone can set maxiter=0, at which point we still want the
        # initial energies to be calculated (the following loop isn't run).
        if np.all(np.isinf(self.population_energies)):
            self.feasible, self.constraint_violation = (
                self._calculate_population_feasibilities(self.population))

            # only work out population energies for feasible solutions
            print("Preparing initial population...")
            self.population_energies[self.feasible] = (
                self._calculate_population_energies(
                    self.population[self.feasible]))

            self._promote_lowest_energy()

        # do the optimization.
        iter_cnt = 0
        for nit in range(1, self.maxiter + 1):
            # evolve the population by a generation
            try:
                next(self)
            except StopIteration:
                warning_flag = True
                if self._nfev > self.maxfun:
                    status_message = 'Maximum number of function evaluations exceeded.'
                elif self._nfev == self.maxfun:
                    status_message = 'Maximum number of function evaluations has been reached.'
                break
            except AbortException:
                status_message = 'Process aborted.'

            std_en = np.std(self.population_energies)
            if self.disp:
                print("Differential evolution step %d: f(x)= %g, std = %g, Np = %d"
                      % (nit, self.population_energies[0], std_en, self.num_population_members))

            if self.callback:
                c = self.tol / (self.convergence + _MACHEPS)
                warning_flag = bool(self.callback(self.x, convergence=c))
                if warning_flag:
                    status_message = ('callback function requested stop early'
                                      ' by returning True')

            # should the solver terminate?
            if warning_flag or self.converged():
                break

            if self.best_energy is not None:
                if abs(self.best_energy - self.population_energies[0]) < self.tol:
                    iter_cnt += 1
                else:
                    iter_cnt = 0

            if iter_cnt >= self.maxiter_conv:
                break

            # if std_en < std_tol:
            if std_en < self.std_conv:
                break

            # Thread abort signal
            if self._abort:
                self._abort = False
                break

            self.best_energy = self.population_energies[0]

        else:
            status_message = ('Maximum number of iterations has been reached.')
            warning_flag = True

        DE_result = OptimizeResult(
            x=self.x,
            fun=self.population_energies[0],
            nfev=self._nfev,
            nit=nit,
            message=status_message,
            success=(warning_flag is not True))

        if self.polish and not np.all(self.integrality):
            # can't polish if all the parameters are integers
            if np.any(self.integrality):
                # set the lower/upper bounds equal so that any integrality
                # constraints work.
                limits, integrality = self.limits, self.integrality
                limits[0, integrality] = DE_result.x[integrality]
                limits[1, integrality] = DE_result.x[integrality]

            polish_method = 'L-BFGS-B'

            if self._wrapped_constraints:
                polish_method = 'trust-constr'

                constr_violation = self._constraint_violation_fn(DE_result.x)
                if np.any(constr_violation > 0.):
                    warnings.warn("differential evolution didn't find a"
                                  " solution satisfying the constraints,"
                                  " attempting to polish from the least"
                                  " infeasible solution", UserWarning)

            result = minimize(self.func,
                              np.copy(DE_result.x),
                              method=polish_method,
                              bounds=self.limits.T,
                              constraints=self.constraints)

            self._nfev += result.nfev
            DE_result.nfev = self._nfev

            # Polishing solution is only accepted if there is an improvement in
            # cost function, the polishing was successful and the solution lies
            # within the bounds.
            if (result.fun < DE_result.fun and
                    result.success and
                    np.all(result.x <= self.limits[1]) and
                    np.all(self.limits[0] <= result.x)):
                DE_result.fun = result.fun
                DE_result.x = result.x
                DE_result.jac = result.jac
                # to keep internal state consistent
                self.population_energies[0] = result.fun
                self.population[0] = self._unscale_parameters(result.x)

        if self._wrapped_constraints:
            DE_result.constr = [c.violation(DE_result.x) for
                                c in self._wrapped_constraints]
            DE_result.constr_violation = np.max(
                np.concatenate(DE_result.constr))
            DE_result.maxcv = DE_result.constr_violation
            if DE_result.maxcv > 0:
                # if the result is infeasible then success must be False
                DE_result.success = False
                DE_result.message = ("The solution does not satisfy the"
                                     " constraints, MAXCV = " % DE_result.maxcv)

        return DE_result

    def _calculate_population_energies(self, population):
        """
        Calculate the energies of a population.
        Parameters
        ----------
        population : ndarray
            An array of parameter vectors normalised to [0, 1] using lower
            and upper limits. Has shape ``(np.size(population, 0), len(x))``.
        Returns
        -------
        energies : ndarray
            An array of energies corresponding to each population member. If
            maxfun will be exceeded during this call, then the number of
            function evaluations will be reduced and energies will be
            right-padded with np.inf. Has shape ``(np.size(population, 0),)``
        """
        num_members = np.size(population, 0)
        # these are the number of function evals left to stay under the
        # maxfun budget
        nfevs = min(num_members, self.maxfun - self._nfev)
        energies = np.full(num_members, np.inf)
        parameters_pop = self._scale_parameters(population)
        calc_energies = self.func(parameters_pop[0:nfevs], *self.args)
        calc_energies = np.squeeze(calc_energies)
        energies[0:nfevs] = calc_energies
        self._nfev += nfevs
        return energies

    def _promote_lowest_energy(self):
        # swaps 'best solution' into first population entry

        idx = np.arange(self.num_population_members)
        feasible_solutions = idx[self.feasible]
        if feasible_solutions.size:
            # find the best feasible solution
            idx_t = np.argmin(self.population_energies[feasible_solutions])
            l = feasible_solutions[idx_t]
        else:
            # no solution was feasible, use 'best' infeasible solution, which
            # will violate constraints the least
            l = np.argmin(np.sum(self.constraint_violation, axis=1))

        self.population_energies[[0, l]] = self.population_energies[[l, 0]]
        self.population[[0, l], :] = self.population[[l, 0], :]
        self.feasible[[0, l]] = self.feasible[[l, 0]]
        self.constraint_violation[[0, l], :] = (self.constraint_violation[[l, 0], :])

    def _constraint_violation_fn(self, x):
        """
        Calculates total constraint violation for all the constraints, for a given
        solution.
        Parameters
        ----------
        x : ndarray
            Solution vector
        Returns
        -------
        cv : ndarray
            Total violation of constraints. Has shape ``(M,)``, where M is the
            number of constraints (if each constraint function only returns one
            value)
        """
        return np.concatenate([c.violation(x) for c in self._wrapped_constraints])

    def _calculate_population_feasibilities(self, population):
        """
        Calculate the feasibilities of a population.
        Parameters
        ----------
        population : ndarray
            An array of parameter vectors normalised to [0, 1] using lower
            and upper limits. Has shape ``(np.size(population, 0), len(x))``.
        Returns
        -------
        feasible, constraint_violation : ndarray, ndarray
            Boolean array of feasibility for each population member, and an
            array of the constraint violation for each population member.
            constraint_violation has shape ``(np.size(population, 0), M)``,
            where M is the number of constraints.
        """
        num_members = np.size(population, 0)
        if not self._wrapped_constraints:
            # shortcut for no constraints
            return np.ones(num_members, bool), np.zeros((num_members, 1))

        parameters_pop = self._scale_parameters(population)

        constraint_violation = np.array([self._constraint_violation_fn(x)
                                         for x in parameters_pop])
        feasible = ~(np.sum(constraint_violation, axis=1) > 0)

        return feasible, constraint_violation

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    '''	
        return self._mapwrapper.__exit__(*args)
    '''

    def _accept_trial(self, energy_trial, feasible_trial, cv_trial,
                      energy_orig, feasible_orig, cv_orig):
        """
        Trial is accepted if:
        * it satisfies all constraints and provides a lower or equal objective
          function value, while both the compared solutions are feasible
        - or -
        * it is feasible while the original solution is infeasible,
        - or -
        * it is infeasible, but provides a lower or equal constraint violation
          for all constraint functions.
        This test corresponds to section III of Lampinen [1]_.
        Parameters
        ----------
        energy_trial : float
            Energy of the trial solution
        feasible_trial : float
            Feasibility of trial solution
        cv_trial : array-like
            Excess constraint violation for the trial solution
        energy_orig : float
            Energy of the original solution
        feasible_orig : float
            Feasibility of original solution
        cv_orig : array-like
            Excess constraint violation for the original solution
        Returns
        -------
        accepted : bool
        """
        if feasible_orig and feasible_trial:
            return energy_trial <= energy_orig
        elif feasible_trial and not feasible_orig:
            return True
        elif not feasible_trial and (cv_trial <= cv_orig).all():
            # cv_trial < cv_orig would imply that both trial and orig are not
            # feasible
            return True

        return False

    def __next__(self):
        """
        Evolve the population by a single generation
        Returns
        -------
        x : ndarray
            The best solution from the solver.
        fun : float
            Value of objective function obtained from the best solution.
        """

        # the population may have just been initialized (all entries are
        # np.inf). If it has you have to calculate the initial energies
        if np.all(np.isinf(self.population_energies)):
            self.feasible, self.constraint_violation = (
                self._calculate_population_feasibilities(self.population))

            # only need to work out population energies for those that are
            # feasible
            self.population_energies[self.feasible] = (
                self._calculate_population_energies(
                    self.population[self.feasible]))

            self._promote_lowest_energy()

        mean_energy = np.mean(self.population_energies)

        if self.dither is not None:
            self.scale = self.random_number_generator.uniform(self.dither[0],
                                                              self.dither[1])

        # update best solution immediately
        for candidate in range(self.num_population_members):
            if self._nfev > self.maxfun:
                raise StopIteration

            # create a trial solution
            trial = self._mutate(candidate)

            # ensuring that it's in the range [0, 1)
            self._ensure_constraint(trial)

            # scale from [0, 1) to the actual parameter value
            parameters = self._scale_parameters(trial)

            # determine the energy of the objective function
            if self._wrapped_constraints:
                cv = self._constraint_violation_fn(parameters)
                feasible = False
                energy = np.inf
                if not np.sum(cv) > 0:
                    # solution is feasible
                    feasible = True
                    energy = self.func(parameters)
                    self._nfev += 1
            else:
                feasible = True
                cv = np.atleast_2d([0.])
                energy = self.func(parameters)
                self._nfev += 1

            # compare trial and population member
            if self._accept_trial(energy, feasible, cv,
                                  self.population_energies[candidate],
                                  self.feasible[candidate],
                                  self.constraint_violation[candidate]):
                self.population[candidate] = trial
                self.population_energies[candidate] = np.squeeze(energy)
                self.feasible[candidate] = feasible
                self.constraint_violation[candidate] = cv

                # if the trial candidate is also better than the best
                # solution then promote it.
                if self._accept_trial(energy, feasible, cv,
                                      self.population_energies[0],
                                      self.feasible[0],
                                      self.constraint_violation[0]):
                    self._promote_lowest_energy()
        """
        if mean_energy > np.mean(self.population_energies):
            self.improved = True
        else:        
            self.improved = False
        """
        self._reduce_population()

        return self.x, self.population_energies[0]

    def _scale_parameters(self, trial):
        """Scale from a number between 0 and 1 to parameters."""
        # trial either has shape (N, ) or (L, N), where L is the number of
        # solutions being scaled
        scaled = self.__scale_arg1 + (trial - 0.5) * self.__scale_arg2
        if np.any(self.integrality):
            i = np.broadcast_to(self.integrality, scaled.shape)
            scaled[i] = np.round(scaled[i])
        return scaled

    def _unscale_parameters(self, parameters):
        """Scale from parameters to a number between 0 and 1."""
        return (parameters - self.__scale_arg1) / self.__scale_arg2 + 0.5

    def _ensure_constraint(self, trial):
        """Make sure the parameters lie between the limits."""
        mask = np.where((trial > 1) | (trial < 0))
        trial[mask] = self.random_number_generator.uniform(size=mask[0].shape)

    def _mutate(self, candidate):
        """Create a trial vector based on a mutation strategy."""
        trial = np.copy(self.population[candidate])

        rng = self.random_number_generator

        fill_point = rng.choice(self.parameter_count)

        if self.strategy in ['currenttobest1exp', 'currenttobest1bin']:
            bprime = self.mutation_func(candidate,
                                        self._select_samples(candidate, 5))
        else:
            bprime = self.mutation_func(self._select_samples(candidate, 5))

        if self.strategy in self._binomial:
            crossovers = rng.uniform(size=self.parameter_count)
            crossovers = crossovers < self.cross_over_probability
            # the last one is always from the bprime vector for binomial
            # If you fill in modulo with a loop you have to set the last one to
            # true. If you don't use a loop then you can have any random entry
            # be True.
            crossovers[fill_point] = True
            trial = np.where(crossovers, bprime, trial)
            return trial

        elif self.strategy in self._exponential:
            i = 0
            crossovers = rng.uniform(size=self.parameter_count)
            crossovers = crossovers < self.cross_over_probability
            while (i < self.parameter_count and crossovers[i]):
                trial[fill_point] = bprime[fill_point]
                fill_point = (fill_point + 1) % self.parameter_count
                i += 1

            return trial

    def _calculate_population_volume(self):
        v = 1.
        for idx in range(self.parameter_count):
            v *= np.max(self.population[:, idx]) - np.min(self.population[:, idx])
        return v

    """
    def _reduce_population(self):
        num_extra_members = 0
        if (self.num_population_members > self.min_pop_membes) and self.improved:
        
            num_extra_members = int(self.num_population_members - self.population_density*self._calculate_population_volume())
            
            if num_extra_members > 0:
            
                if self.num_population_members - num_extra_members < self.min_pop_membes:
                    num_extra_members = self.num_population_members - self.min_pop_membes
                
                idxs = np.argsort(self.population_energies)[-num_extra_members:]
                
                self.population = np.delete(self.population, idxs, axis = 0)
                self.population_energies = np.delete(self.population_energies, idxs)
                self.feasible = np.delete(self.feasible, idxs)
                self.constraint_violation = np.delete(self.constraint_violation, idxs, axis = 0)
                self.num_population_members -= num_extra_members
                self.population_shape = (self.num_population_members, self.parameter_count)
        
        #print(self.num_population_members, num_extra_members, np.mean(self.population_energies), end = '\r')
    """

    def _reduce_population(self):
        if self.num_population_members > self.min_pop_membes:
            idxs = np.argwhere(self.population_energies > self.threshold).T[0]
            if len(idxs) > 0:
                print("Number of weak members ot of a total {0}: {1}".format(
                    len(self.population_energies), len(idxs)))
                self.population = np.delete(self.population, idxs, axis=0)
                self.population_energies = np.delete(self.population_energies, idxs)
                self.feasible = np.delete(self.feasible, idxs)
                self.constraint_violation = np.delete(self.constraint_violation, idxs, axis=0)
                self.num_population_members -= len(idxs)
                self.population_shape = (self.num_population_members, self.parameter_count)

    def _best1(self, samples):
        """best1bin, best1exp"""
        r0, r1 = samples[:2]
        return (self.population[0] + self.scale *
                (self.population[r0] - self.population[r1]))

    def _rand1(self, samples):
        """rand1bin, rand1exp"""
        r0, r1, r2 = samples[:3]
        return (self.population[r0] + self.scale *
                (self.population[r1] - self.population[r2]))

    def _randtobest1(self, samples):
        """randtobest1bin, randtobest1exp"""
        r0, r1, r2 = samples[:3]
        bprime = np.copy(self.population[r0])
        bprime += self.scale * (self.population[0] - bprime)
        bprime += self.scale * (self.population[r1] -
                                self.population[r2])
        return bprime

    def _currenttobest1(self, candidate, samples):
        """currenttobest1bin, currenttobest1exp"""
        r0, r1 = samples[:2]
        bprime = (self.population[candidate] + self.scale *
                  (self.population[0] - self.population[candidate] +
                   self.population[r0] - self.population[r1]))
        return bprime

    def _best2(self, samples):
        """best2bin, best2exp"""
        r0, r1, r2, r3 = samples[:4]
        bprime = (self.population[0] + self.scale *
                  (self.population[r0] + self.population[r1] -
                   self.population[r2] - self.population[r3]))

        return bprime

    def _rand2(self, samples):
        """rand2bin, rand2exp"""
        r0, r1, r2, r3, r4 = samples
        bprime = (self.population[r0] + self.scale *
                  (self.population[r1] + self.population[r2] -
                   self.population[r3] - self.population[r4]))

        return bprime

    def _select_samples(self, candidate, number_samples):
        """
        obtain random integers from range(self.num_population_members),
        without replacement. You can't have the original candidate either.
        """
        idxs = list(range(self.num_population_members))
        idxs.remove(candidate)
        self.random_number_generator.shuffle(idxs)
        idxs = idxs[:number_samples]
        return idxs

class _ConstraintWrapper:
    """Object to wrap/evaluate user defined constraints.
    Very similar in practice to `PreparedConstraint`, except that no evaluation
    of jac/hess is performed (explicit or implicit).
    If created successfully, it will contain the attributes listed below.
    Parameters
    ----------
    constraint : {`NonlinearConstraint`, `LinearConstraint`, `Bounds`}
        Constraint to check and prepare.
    x0 : array_like
        Initial vector of independent variables.
    Attributes
    ----------
    fun : callable
        Function defining the constraint wrapped by one of the convenience
        classes.
    bounds : 2-tuple
        Contains lower and upper bounds for the constraints --- lb and ub.
        These are converted to ndarray and have a size equal to the number of
        the constraints.
    """

    def __init__(self, constraint, x0):
        self.constraint = constraint

        if isinstance(constraint, NonlinearConstraint):
            def fun(x):
                return np.atleast_1d(constraint.fun(x))
        elif isinstance(constraint, LinearConstraint):
            def fun(x):
                if issparse(constraint.A):
                    A = constraint.A
                else:
                    A = np.atleast_2d(constraint.A)
                return A.dot(x)
        elif isinstance(constraint, Bounds):
            def fun(x):
                return x
        else:
            raise ValueError("`constraint` of an unknown type is passed.")

        self.fun = fun

        lb = np.asarray(constraint.lb, dtype=float)
        ub = np.asarray(constraint.ub, dtype=float)

        f0 = fun(x0)
        m = f0.size

        if lb.ndim == 0:
            lb = np.resize(lb, m)
        if ub.ndim == 0:
            ub = np.resize(ub, m)

        self.bounds = (lb, ub)

    def __call__(self, x):
        return np.atleast_1d(self.fun(x))

    def violation(self, x):
        """How much the constraint is exceeded by.
        Parameters
        ----------
        x : array-like
            Vector of independent variables
        Returns
        -------
        excess : array-like
            How much the constraint is exceeded by, for each of the
            constraints specified by `_ConstraintWrapper.fun`.
        """
        ev = self.fun(np.asarray(x))

        excess_lb = np.maximum(self.bounds[0] - ev, 0)
        excess_ub = np.maximum(ev - self.bounds[1], 0)

        return excess_lb + excess_ub
