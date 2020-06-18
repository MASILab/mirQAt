from mirqat import __version__


def test_version():
    assert __version__ == '0.1.0'


from mirqat.main import *

p = Path("dcm_root")

def path_exists():
    assert p.exists() == True

def test_instance():
    assert dcm_instance(p) == (361, 361, 0)

def test_slice_distance():
    assert dcm_slicedistance(p) == 1