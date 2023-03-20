/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Copyright (C) 2023 Intel Corporation */

/*!
 * \file
 *
 * This file contains the dummy references to secret_prov_verify exported functions (this is to
 * force symbols from libsecret_prov_verify.a to be exported in our MAA version; note that by
 * default unused symbols from a linked static library are *not* exported).
 */

#include <stddef.h>

#include "secret_prov.h"

static __attribute__((used)) void* dummy_secret_prov_symbols_table[] = {
    secret_provision_start_server,
    secret_provision_read,
    secret_provision_write,
    secret_provision_close,
};
