#
# Project configuration, options, modules, scripts
#

project(
    'ra-tls-maa',
    'c', 'cpp',
    version: '0.1',
    license: 'LGPLv3+',

    meson_version: '>=0.56',

    default_options: [
        'c_std=c11',
    ],
)

pkgconfig = find_program('pkg-config')

cc = meson.get_compiler('c')

add_project_arguments(
    '-Wa,--noexecstack',

    '-Wall',
    '-Wextra',

    '-Wmissing-prototypes',
    '-Wstrict-prototypes',
    '-Wwrite-strings',

    cc.get_supported_arguments(
        '-Wtrampolines',
        '-Wnull-dereference',
    ),

    language: 'c')

release_mode = get_option('buildtype') == 'release'
if release_mode
    add_project_arguments('-DNDEBUG', language: 'c')
endif

curl_proj = subproject('curl-7.84.0')
libcurl_dep = curl_proj.get_variable('curl_minimal_dep')

cjson_proj = subproject('cJSON-1.7.12')
cjson_dep = cjson_proj.get_variable('cjson_dep')

threads_dep = dependency('threads')

mbedtls_dep = dependency('mbedtls_gramine', static: true)

# RA-TLS with MAA

ra_tls_map = meson.current_source_dir() / 'src' / 'ra_tls.map'
ra_tls_link_args = [
    '-Wl,--version-script=@0@'.format(ra_tls_map),
]

ra_tls_dep = dependency('ra_tls_gramine')
ra_tls_libdir = ra_tls_dep.get_variable(pkgconfig: 'libdir')
ra_tls_includedir = ra_tls_dep.get_variable(pkgconfig: 'includedir') + '/gramine'

ra_tls_verify_lib = cc.find_library('ra_tls_verify', dirs: ra_tls_libdir)
ra_tls_util_lib = cc.find_library('sgx_util', dirs: ra_tls_libdir)

libra_tls_verify_maa = shared_library('ra_tls_verify_maa',
    'src' / 'ra_tls_verify_maa.c',

    include_directories: ra_tls_includedir,
    link_args: ra_tls_link_args,
    dependencies: [
        cjson_dep,
        libcurl_dep,
        mbedtls_dep,
        ra_tls_util_lib,
        ra_tls_verify_lib,
    ],
    install: true,
    install_rpath: get_option('prefix') / get_option('libdir'),
)

# Secret Prov with MAA

secret_prov_map = meson.current_source_dir() / 'src' / 'secret_prov.map'
secret_prov_link_args = [
    '-Wl,--version-script=@0@'.format(secret_prov_map),
]

secret_prov_dep = dependency('secret_prov_gramine')
secret_prov_libdir = secret_prov_dep.get_variable(pkgconfig: 'libdir')
secret_prov_includedir = secret_prov_dep.get_variable(pkgconfig: 'includedir') + '/gramine'

secret_prov_verify_lib = cc.find_library('secret_prov_verify', dirs: secret_prov_libdir)

libsecret_prov_verify_maa = shared_library('secret_prov_verify_maa',
    'src' / 'secret_prov_verify_maa.c',
    'src' / 'ra_tls_verify_maa.c',

    include_directories: secret_prov_includedir,
    link_args: secret_prov_link_args,
    dependencies: [
        cjson_dep,
        libcurl_dep,
        mbedtls_dep,
        ra_tls_util_lib,
        ra_tls_verify_lib,
        secret_prov_verify_lib,
        threads_dep,
    ],
    install: true,
    install_rpath: get_option('prefix') / get_option('libdir'),
)
