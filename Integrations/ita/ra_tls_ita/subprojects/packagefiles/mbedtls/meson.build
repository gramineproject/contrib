project('mbedtls', 'c', version: '3.4.0')

mbedtls_curl_libs = custom_target('mbedtls_curl',
    command: [
        find_program('compile-curl.sh'),
        '@CURRENT_SOURCE_DIR@',
        '@CURRENT_SOURCE_DIR@/mbedtls-mbedtls-3.4.0',
        meson.current_build_dir(),
        '@PRIVATE_DIR@',
        meson.build_root() / 'subprojects',
        '@OUTPUT@',
    ],

    input: ['mbedtls-mbedtls-3.4.0/Makefile'],

    output: [
        'libmbedcrypto.a',
        'libmbedtls.a',
        'libmbedx509.a',
    ],

    build_by_default: true,
)

mbedtls_inc = include_directories('include', 'mbedtls-mbedtls-3.4.0/include')

mbedtls_curl_dep = declare_dependency(
    # HACK: Apparently Meson considers the `mbedtls_curl_libs` to be "not linkable", because it has
    # multiple outputs; however, it allows picking the outputs one by one.
    link_with: [mbedtls_curl_libs[0], mbedtls_curl_libs[1], mbedtls_curl_libs[2]],
    include_directories: mbedtls_inc,
    compile_args: '-DMBEDTLS_CONFIG_FILE="mbedtls/config-min.h"',
)
