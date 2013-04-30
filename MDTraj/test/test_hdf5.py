import numpy as np
from mdtraj.hdf5 import HDF5Trajectory
from mdtraj.testing import get_fn, eq
from nose.tools import assert_raises

def test_write_coordinates():
    coordinates = np.random.randn(4, 10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates)
    
    with HDF5Trajectory('f.h5') as f:
        yield lambda: eq(f.root.coordinates[:], coordinates)
        yield lambda: eq(str(f.root.coordinates.attrs['units']), 'nanometers')


def test_write_coordinates_reshape():
    coordinates = np.random.randn(10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates)
    
    with HDF5Trajectory('f.h5') as f:
        yield lambda: eq(f.root.coordinates[:], coordinates.reshape(1,10,3))
        yield lambda: eq(str(f.root.coordinates.attrs['units']), 'nanometers')
    

def test_write_multiple():
    coordinates = np.random.randn(4, 10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates)
        f.write(coordinates)
    
    with HDF5Trajectory('f.h5') as f:
        yield lambda: eq(f.root.coordinates[:], np.vstack((coordinates, coordinates)))

def test_write_inconsistent():
    coordinates = np.random.randn(4, 10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates)
        with assert_raises(ValueError):
            # since the first frames we saved didn't contain velocities, we
            # can't save more velocities
            f.write(coordinates, velocities=coordinates)

def test_write_inconsistent_2():
    coordinates = np.random.randn(4, 10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates, velocities=coordinates)
        with assert_raises(ValueError):
            # we're saving a deficient set of data, since before we wrote
            # more information.
            f.write(coordinates)
            
def test_write_units():
    "simtk.units are automatically converted into MD units for storage on disk"
    from simtk.unit import angstroms, nanometers, year, picosecond, Quantity
    coordinates = Quantity(np.random.randn(4, 10,3), angstroms)
    velocities = Quantity(np.random.randn(4, 10,3), angstroms/year)
    
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates, velocities=velocities)

    with HDF5Trajectory('f.h5') as f:
        yield lambda: eq(f.root.coordinates[:], coordinates.value_in_unit(nanometers))
        yield lambda: eq(str(f.root.coordinates.attrs['units']), 'nanometers')
        
        yield lambda: eq(f.root.velocities[:], velocities.value_in_unit(nanometers/picosecond))
        yield lambda: eq(str(f.root.velocities.attrs['units']), 'nanometers/picosecond')

def test_write_units_mismatch():
    from simtk.unit import angstroms, nanometers, picosecond, Quantity
    velocoties = Quantity(np.random.randn(4, 10,3), angstroms/picosecond)
    
    with HDF5Trajectory('f.h5', 'w') as f:
        with assert_raises(TypeError):
            # if you try to write coordinates that are unitted and not 
            # in the correct units, we find that
            f.write(coordinates=velocoties)


def test_topology():
    from mdtraj import trajectory, topology
    top = trajectory.load_pdb(get_fn('native.pdb')).topology

    with HDF5Trajectory('f.h5', 'w') as f:
        f.topology = top
    
    with HDF5Trajectory('f.h5') as f:
        topology.equal(f.topology, top)


def test_read_0():
    coordinates = np.random.randn(4, 10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates, lambdaValue=np.array([1,2,3,4]))

    with HDF5Trajectory('f.h5') as f:
        got = f.read()
        yield lambda: eq(got.coordinates, coordinates)
        yield lambda: eq(got.velocities, None)
        yield lambda: eq(got.lambdaValue, np.array([1,2,3,4]))


def test_read_1():
    import simtk.unit as units
    coordinates = units.Quantity(np.random.randn(4, 10,3), units.angstroms)
    velocities = units.Quantity(np.random.randn(4, 10,3), units.angstroms/units.years)


    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates, velocities=velocities)

    with HDF5Trajectory('f.h5') as f:
        got = f.read()
        yield lambda: eq(got.coordinates, coordinates.value_in_unit(units.nanometers))
        yield lambda: eq(got.velocities, velocities.value_in_unit(units.nanometers/units.picoseconds))

def test_read_slice_0():
    coordinates = np.random.randn(4, 10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates, lambdaValue=np.array([1,2,3,4]))

    with HDF5Trajectory('f.h5') as f:
        got = f.read(n_frames=2)
        yield lambda: eq(got.coordinates, coordinates[:2])
        yield lambda: eq(got.velocities, None)
        yield lambda: eq(got.lambdaValue, np.array([1,2]))
        
def test_read_slice_1():
    coordinates = np.random.randn(4, 10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates)

    with HDF5Trajectory('f.h5') as f:
        got = f.read(n_frames=2)
        yield lambda: eq(got.coordinates, coordinates[:2])
        yield lambda: eq(got.velocities, None)

        got = f.read(n_frames=2)
        yield lambda: eq(got.coordinates, coordinates[2:])
        yield lambda: eq(got.velocities, None)

def test_read_slice_2():
    coordinates = np.random.randn(4, 10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates, lambdaValue=np.arange(4))

    with HDF5Trajectory('f.h5') as f:
        got = f.read(atom_indices=np.array([0,1]))
        yield lambda: eq(got.coordinates, coordinates[:, [0,1], :])
        yield lambda: eq(got.lambdaValue, np.arange(4))

def test_read_slice_3():
    coordinates = np.random.randn(4, 10,3)
    with HDF5Trajectory('f.h5', 'w') as f:
        f.write(coordinates, lambdaValue=np.arange(4))

    with HDF5Trajectory('f.h5') as f:
        got = f.read(stride=2, atom_indices=np.array([0,1]))
        yield lambda: eq(got.coordinates, coordinates[::2, [0,1], :])
        yield lambda: eq(got.lambdaValue, np.arange(4)[::2])