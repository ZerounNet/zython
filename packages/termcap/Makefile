
all: wasm native

include ../build/Makefile-vars

# See https://ftp.gnu.org/gnu/termcap/
# Not likely to change -- it hasn't in over 20 years!
VERSION = 1.3.1
TARBALL = ${UPSTREAM}/termcap-${VERSION}.tar.gz
URL = https://ftp.gnu.org/gnu/termcap/termcap-${VERSION}.tar.gz


include ../build/Makefile-rules

##################
# NATIVE
##################

${DIST_NATIVE}/.built: ${BUILD_NATIVE}/.build
	cp src/config.h ${BUILD_NATIVE}
	cd ${BUILD_NATIVE} && \
		CC="zig cc ${ZIG_NATIVE_CFLAGS_GNU} -DHAVE_CONFIG_H=1 " AR="zig ar" ./configure --prefix=${DIST_NATIVE} && \
		make -j8 && \
		make install
	touch ${DIST_NATIVE}/.built


##################
# WASM
##################

${DIST_WASM}/.built: ${BUILD_WASM}/.build
	cp src/config.h ${BUILD_WASM}
	cd ${BUILD_WASM} && \
		RANLIB="zig ranlib" \
		AR="zig ar" \
		CC="zig-fPIC cc -Oz -DHAVE_CONFIG_H=1 " \
		./configure  --build=`./build-aux/config.guess` --host=none --prefix="${DIST_WASM}" && \
		make -j8 && \
		make install
	touch ${DIST_WASM}/.built
