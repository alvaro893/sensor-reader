from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("*.pyx")
)


# from distutils.core import setup
# from distutils.extension import Extension
# from Cython.Distutils import build_ext
#
#
# ext_modules = [
#     Extension("data", ["data.pyx"]),
#     Extension("user", ["user.pyx"],include_dirs = ['myPackageDir'])
#     ]
#
# setup(
#   name = 'app',
#   cmdclass = {'build_ext': build_ext},
#   ext_modules = ext_modules
# )