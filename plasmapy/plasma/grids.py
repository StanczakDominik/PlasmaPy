"""
Defines the AbstractGrid class and child classes
"""

__all__ = [
    "AbstractGrid",
    "CartesianGrid",
]


from abc import ABC, abstractmethod
import astropy.units as u
import numpy as np
import pytest
import warnings
from typing import Union

class AbstractGrid(ABC):
    """
    Abstract grid represents a 3D grid of positions. The grid is stored as an
    np.ndarray, while the units associated with each dimension are stored
    separately.
    """

    # TODO: add appropriate typing here on start, stop, num
    # start/stop can be -> number(int,float), ndarray, u.quantity, list of numbers or u.quantities
    # units can be astropy.units.core.Unit or list of same
    def __init__(self,
                 start = 0,
                 stop = 1,
                 num  = 100,
                 grid=None,
                 units = None):

        # Load or create the grid
        if grid is None:
            self._make_grid(start=start, stop=stop, num=num)
        else:
            self._load_grid(grid=grid, units=units)

        # Setup method contains uther initialization stuff
        self._setup()


    def _setup(self):
        # Properties
        self._coordinate_system = None
        self._regular_grid = None

    @property
    def grid(self):
        """Grid of positional values."""
        return self._grid

    @property
    def regular_grid(self):
        """
        Value of regular_grid
        If None, calculate
        """
        if self._regular_grid is None:
            self._detect_regular_grid()
        return self._regular_grid


    @property
    def shape(self):
        return self._grid.shape

    @property
    def unit(self):
        if (self._units[0] == self._units[1] and
            self._units[0] == self._units[2]):
            return self._units[0]
        else:
            raise ValueError("Array dimensions do not all have the same "
                             f"units: {self._units}")

    @property
    def units(self):
        return self._units

    @property
    def unit0(self):
        return self._units[0]

    @property
    def unit1(self):
        return self._units[1]

    @property
    def unit2(self):
        return self._units[2]

    @property
    def ax0(self):
        return self._grid[:,0,0,0]

    @property
    def ax1(self):
        return self._grid[0,:,0,1]

    @property
    def ax2(self):
        return self._grid[0,0,:,2]

    @property
    def dax0(self):
        return np.mean(np.gradient(self.ax0))

    @property
    def dax1(self):
        return np.mean(np.gradient(self.ax1))

    @property
    def dax2(self):
        return np.mean(np.gradient(self.ax2))

    @property
    def arr0(self):
        return self._grid[...,0]

    @property
    def arr1(self):
        return self._grid[...,1]

    @property
    def arr2(self):
        return self._grid[...,2]


    def _validate(self):
        """
        Checks to make sure that the grid parameters are
        consistent with the coordinate system and units selected

        """
        return True


    def _load_grid(self, grid=None, units=None):

        # If single values are given, expand to a list of appropriate length
        if isinstance(units, u.core.Unit):
            units = [units] * 3

        # Determine units from grid or units keyword (in that order)
        if hasattr(grid, 'unit'):
            self._units = [grid.unit] * 3
        elif units is not None:
            self._units = units
        else:
            self._units = [u.dimensionless_unscaled] * 3

        self._grid = grid

        # Check to make sure that the object created satisfies any
        # requirements: eg. units correspond to the coordinate system
        self._validate()


    def _make_grid(self, start=0, stop=1, num = 100):

        # If single values are given, expand to a list of appropriate length
        if isinstance(stop, (int, float, u.Quantity)):
            stop = [stop] * 3
        if isinstance(start, (int, float, u.Quantity)):
            start = [start] * 3
        if isinstance(num, (int, float, u.Quantity)):
            num = [num] * 3


        # Extract units from input arrays (if they are there), then
        # remove the units from those arrays
        units = [u.dimensionless_unscaled] * 3
        for i in range(3):
            # Determine unit of stop entry
            if hasattr(stop[i], 'unit'):
                stop_unit = stop[i].unit
            else:
                stop_unit = u.dimensionless_unscaled

            # Determine unit of start entry
            if hasattr(start[i], 'unit'):
                start_unit = start[i].unit
            else:
                start_unit = u.dimensionless_unscaled

            # If stop and start units are the same, use the same units for
            # both.
            if stop_unit == start_unit:
                units[i] = stop_unit

            # If stop and start units are compatible, convert them to be the
            # same
            else:
                try:
                    start[i] = start[i].to(stop_unit)
                    units[i] = stop_unit
                except u.UnitConversionError:
                    raise ValueError(f"Units of stop ({stop_unit}) and "
                                     f"start ({start_unit}) are not "
                                     "compatible.")
            # Remove units
            stop[i] = stop[i].value
            start[i] = start[i].value

        # Construct the axis arrays
        ax0 = np.linspace(start[0], stop[0], num=num[0])
        ax1 = np.linspace(start[1], stop[1], num=num[1])
        ax2 = np.linspace(start[2], stop[2], num=num[2])


        # Construct the coordinate arrays and grid
        arr0, arr1, arr2 = np.meshgrid(ax0, ax1, ax2, indexing='ij')
        grid = np.zeros([ax0.size, ax1.size, ax2.size, 3])
        grid[...,0] = arr0
        grid[...,1] = arr1
        grid[...,2] = arr2


        self._units = units
        self._grid = grid

        # Check to make sure that the object created satisfies any
        # requirements: eg. units correspond to the coordinate system
        self._validate()

    def _detect_regular_grid(self, tol=1e-6):
        """
        Determine whether a grid is regular (uniformly spaced) by computing the
        variance of the grid gradients.
        """
        variance = np.zeros([3])
        dx = np.gradient(self.arr0, axis=0)
        variance[0] = np.std(dx) / np.mean(dx)
        dy = np.gradient(self.arr1, axis=1)
        variance[1] = np.std(dy) / np.mean(dy)
        dz = np.gradient(self.arr2, axis=2)
        variance[2] = np.std(dz) / np.mean(dz)

        self._regular_grid = np.allclose(variance, 0.0, atol=tol)






class CartesianGrid(AbstractGrid):


    def _validate(self):
        # Check that all units are lengths
        for i in range(3):
            try:
                (self.units[i].to(u.m))
            except u.UnitConversionError:
                raise ValueError("Units of grid are not valid for a Cartesian "
                                 f"grid: {self.units}.")

    @property
    def xarr(self):
        """
        The 3D array of x values
        """
        return self.arr0

    @property
    def yarr(self):
        """
        The 3D array of y values
        """
        return self.arr1

    @property
    def zarr(self):
        """
        The 3D array of z values
        """
        return self.arr2

    @property
    def xaxis(self):
        """
        The x-axis
        """
        return self.ax0

    @property
    def yaxis(self):
        """
        The y-axis (only valid for a uniform grid)
        """
        return self.ax1

    @property
    def zaxis(self):
        """
        The z-axis (only valid for a uniform grid)
        """
        return self.ax2

    @property
    def dx(self):
        """
        Calculated dx (only valid for a uniform grid)
        """
        return np.mean(np.gradient(self.xaxis))

    @property
    def dy(self):
        """
        Calculated dy (only valid for a uniform grid)
        """
        return np.mean(np.gradient(self.yaxis))

    @property
    def dz(self):
        """
        Calculated dz (only valid for a uniform grid)
        """
        return np.mean(np.gradient(self.zaxis))

    @property
    def distance_from_origin(self):
        """
        The 3D array of the radial position of each point from the
        origin
        """
        return np.sqrt(self.xaxis ** 2 + self.yaxis ** 2 + self.zaxis ** 2)




class IrregularCartesianGrid(CartesianGrid):
    """
    A Cartesian grid in which the _make_grid method produces an irregularly
    spaced grid (rather than a uniform one)
    """
    pass



class CylindricalGrid(AbstractGrid):
    """
    A grid with dimensions (r, theta, z) and units (length, angle, length)
    """
    pass


class SphericalGrid(AbstractGrid):
    """
    A grid with dimensions (r, theta, phi) and units (length, angle, angle)
    """
    pass