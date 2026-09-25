import copy, os, logging

FILAMENT_LOAD_TEMP_UNKNOWN                      = 250
FILAMENT_UNLOAD_TEMP_UNKNOWN                    = 250
FILAMENT_CLEAN_NOZZLE_TEMP_UNKNOWN              = 170
FILAMENT_FLOW_TEMP_UNKNOWN                      = 220
FILAMENT_FLOW_K_UNKNOWN                         = 0.02
FILAMENT_FLOW_K_UNKNOWN_02                      = 0.20
FILAMENT_FLOW_K_UNKNOWN_04                      = 0.02
FILAMENT_FLOW_K_UNKNOWN_06                      = 0.012
FILAMENT_FLOW_K_UNKNOWN_08                      = 0.008
FILAMENT_FLOW_SLOW_V_UNKNOWN                    = 0.63
FILAMENT_FLOW_SLOW_V_UNKNOWN_02                 = 0.17
FILAMENT_FLOW_SLOW_V_UNKNOWN_04                 = 0.63
FILAMENT_FLOW_SLOW_V_UNKNOWN_06                 = 1.386
FILAMENT_FLOW_SLOW_V_UNKNOWN_08                 = 2.44
FILAMENT_FLOW_FAST_V_UNKNOWN                    = 4.99
FILAMENT_FLOW_FAST_V_UNKNOWN_02                 = 0.83
FILAMENT_FLOW_FAST_V_UNKNOWN_04                 = 4.99
FILAMENT_FLOW_FAST_V_UNKNOWN_06                 = 4.99
FILAMENT_FLOW_FAST_V_UNKNOWN_08                 = 4.99
FILAMENT_FLOW_ACCEL_UNKNOWN                     = 153.6
FILAMENT_FLOW_ACCEL_UNKNOWN_02                  = 40.5
FILAMENT_FLOW_ACCEL_UNKNOWN_04                  = 153.6
FILAMENT_FLOW_ACCEL_UNKNOWN_06                  = 339.6
FILAMENT_FLOW_ACCEL_UNKNOWN_08                  = 598.3
FILAMENT_FLOW_K_MIN_UNKNOWN                     = 0
FILAMENT_FLOW_K_MIN_UNKNOWN_02                  = 0
FILAMENT_FLOW_K_MIN_UNKNOWN_04                  = 0
FILAMENT_FLOW_K_MIN_UNKNOWN_06                  = 0
FILAMENT_FLOW_K_MIN_UNKNOWN_08                  = 0
FILAMENT_FLOW_K_MAX_UNKNOWN                     = 0.065
FILAMENT_FLOW_K_MAX_UNKNOWN_02                  = 0.300
FILAMENT_FLOW_K_MAX_UNKNOWN_04                  = 0.100
FILAMENT_FLOW_K_MAX_UNKNOWN_06                  = 0.070
FILAMENT_FLOW_K_MAX_UNKNOWN_08                  = 0.050

FILAMENT_IS_SOFT_UNKNOWN                        = False
FILAMENT_PARAMETER_VERSION                      = '0.0.10'

NOT_ALLOW_TO_FLOW_CALIBRATE_02 = {
    'PLA': ['Wood'],
    'PLA-CF': ['*'],
    'PETG-CF': ['*'],
    'TPU': ['*'],
    'PVA': ['*'],
    'PA': ['*'],
    'PC': ['*'],
}

FILAMENT_PARA_CFG_FILE                          = 'filament_parameters.json'
FILAMENT_PARA_CFG_DEFAULT = {
    'version': '0.0.9',
    'hard_filaments_max_flow_k': 0.40,
    'soft_filaments_max_flow_k': 0.50,
    'PLA': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 170,
                'is_soft': False,
                'flow_temp': 220,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.02,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.99,
                    '06': 4.99,
                    '08': 4.99
                },
                'flow_accel': {
                    '02': 40.5,
                    '04': 153.6,
                    '06': 339.6,
                    '08': 598.3
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.040,
                    '06': 0.030,
                    '08': 0.020
                },
            },
        },
        'vendor_Snapmaker': {
            'sub_generic': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 170,
                'is_soft': False,
                'flow_temp': 220,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.02,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.99,
                    '06': 4.99,
                    '08': 4.99
                },
                'flow_accel': {
                    '02': 40.5,
                    '04': 153.6,
                    '06': 339.6,
                    '08': 598.3
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.040,
                    '06': 0.030,
                    '08': 0.020
                },
            },
            'sub_Silk': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 180,
                'is_soft': False,
                'flow_temp': 230,
                'flow_k': {
                    '02': 0.150,
                    '04': 0.020,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.16,
                    '06': 4.16,
                    '08': 4.16
                },
                'flow_accel': {
                    '02': 40.5,
                    '04': 153.6,
                    '06': 339.6,
                    '08': 598.3
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.250,
                    '04': 0.025,
                    '06': 0.020,
                    '08': 0.015
                },
            },
            'sub_SnapSpeed': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 170,
                'is_soft': False,
                'flow_temp': 220,
                'flow_k': {
                    '02': 0.200,
                    '04': 0.020,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 8.32,
                    '06': 8.32,
                    '08': 8.32
                },
                'flow_accel': {
                    '02': 39.9,
                    '04': 151.4,
                    '06': 334.7,
                    '08': 589.7
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.010,
                    '06': 0.005,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.250,
                    '04': 0.028,
                    '06': 0.020,
                    '08': 0.015
                },
            },
            'sub_Matte': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 165,
                'is_soft': False,
                'flow_temp': 215,
                'flow_k': {
                    '02': 0.200,
                    '04': 0.025,
                    '06': 0.015,
                    '08': 0.009
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.442
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 9.15,
                    '06': 9.15,
                    '08': 9.15
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.8,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.010,
                    '06': 0.005,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.250,
                    '04': 0.030,
                    '06': 0.025,
                    '08': 0.020
                },
            },
            'sub_Wood': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 170,
                'is_soft': False,
                'flow_temp': 220,
                'flow_k': {
                    '02': 0.200,
                    '04': 0.022,
                    '06': 0.014,
                    '08': 0.009
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.442
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 7.48,
                    '06': 7.48,
                    '08': 7.48
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.8,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.010,
                    '06': 0.005,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.250,
                    '04': 0.035,
                    '06': 0.030,
                    '08': 0.025
                },
            },
        },
        'vendor_Polymaker': {
            'sub_generic': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 170,
                'is_soft': False,
                'flow_temp': 220,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.02,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.99,
                    '06': 4.99,
                    '08': 4.99
                },
                'flow_accel': {
                    '02': 40.5,
                    '04': 153.6,
                    '06': 339.6,
                    '08': 598.3
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.040,
                    '06': 0.030,
                    '08': 0.020
                },
            },
            'sub_Silk': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 180,
                'is_soft': False,
                'flow_temp': 230,
                'flow_k': {
                    '02': 0.150,
                    '04': 0.020,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.16,
                    '06': 4.16,
                    '08': 4.16
                },
                'flow_accel': {
                    '02': 40.5,
                    '04': 153.6,
                    '06': 339.6,
                    '08': 598.3
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.250,
                    '04': 0.025,
                    '06': 0.020,
                    '08': 0.015
                },
            },
        },
    },
    'PLA-CF': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 170,
                'is_soft': False,
                'flow_temp': 220,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.02,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.99,
                    '06': 4.99,
                    '08': 4.99
                },
                'flow_accel': {
                    '02': 40.5,
                    '04': 153.6,
                    '06': 339.6,
                    '08': 598.3
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.040,
                    '06': 0.030,
                    '08': 0.020
                },
            },
        },
    },
    'TPU': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 190,
                'is_soft': True,
                'flow_temp': 240,
                'flow_k': {
                    '02': 0.30,
                    '04': 0.25,
                    '06': 0.20,
                    '08': 0.12
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.4,
                    '06': 0.4,
                    '08': 0.4
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 1.33,
                    '06': 1.33,
                    '08': 1.33
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.8,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.20,
                    '04': 0.15,
                    '06': 0.10,
                    '08': 0.05
                },
                'flow_k_max': {
                    '02': 0.36,
                    '04': 0.36,
                    '06': 0.30,
                    '08': 0.25
                },
            },
        },
        'vendor_Snapmaker': {
            'sub_generic': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 190,
                'is_soft': True,
                'flow_temp': 240,
                'flow_k': {
                    '02': 0.30,
                    '04': 0.25,
                    '06': 0.20,
                    '08': 0.12
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.4,
                    '06': 0.4,
                    '08': 0.4
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 1.33,
                    '06': 1.33,
                    '08': 1.33
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.8,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.20,
                    '04': 0.15,
                    '06': 0.10,
                    '08': 0.05
                },
                'flow_k_max': {
                    '02': 0.36,
                    '04': 0.36,
                    '06': 0.30,
                    '08': 0.25
                },
            },
            'sub_95A HF': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 180,
                'is_soft': True,
                'flow_temp': 230,
                'flow_k': {
                    '02': 0.28,
                    '04': 0.23,
                    '06': 0.18,
                    '08': 0.12
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.40,
                    '06': 0.69,
                    '08': 1.22
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 3.742,
                    '06': 3.742,
                    '08': 3.742
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.8,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.20,
                    '04': 0.15,
                    '06': 0.10,
                    '08': 0.05
                },
                'flow_k_max': {
                    '02': 0.36,
                    '04': 0.36,
                    '06': 0.30,
                    '08': 0.25
                },
            }
        },
    },
    'PETG': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 270,
                'unload_temp': 270,
                'clean_nozzle_temp': 205,
                'is_soft': False,
                'flow_temp': 255,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.030,
                    '06': 0.015,
                    '08': 0.010
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.99,
                    '06': 4.99,
                    '08': 4.99
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0.003,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
            'sub_HF': {
                'load_temp': 270,
                'unload_temp': 270,
                'clean_nozzle_temp': 170,
                'is_soft': False,
                'flow_temp': 220,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.02,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 6.65,
                    '06': 6.65,
                    '08': 6.65
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.250,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
        'vendor_Snapmaker': {
            'sub_generic': {
                'load_temp': 270,
                'unload_temp': 270,
                'clean_nozzle_temp': 205,
                'is_soft': False,
                'flow_temp': 255,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.050,
                    '06': 0.030,
                    '08': 0.010
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.99,
                    '06': 4.99,
                    '08': 4.99
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0.003,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
            'sub_HF': {
                'load_temp': 270,
                'unload_temp': 270,
                'clean_nozzle_temp': 195,
                'is_soft': False,
                'flow_temp': 245,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.02,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 8.3,
                    '06': 8.3,
                    '08': 8.3
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.040,
                    '06': 0.030,
                    '08': 0.020
                },
            },
        },
        'vendor_Polymaker': {
            'sub_generic': {
                'load_temp': 270,
                'unload_temp': 270,
                'clean_nozzle_temp': 205,
                'is_soft': False,
                'flow_temp': 255,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.050,
                    '06': 0.030,
                    '08': 0.010
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.99,
                    '06': 4.99,
                    '08': 4.99
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0.003,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
            'sub_HF': {
                'load_temp': 270,
                'unload_temp': 270,
                'clean_nozzle_temp': 195,
                'is_soft': False,
                'flow_temp': 245,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.02,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 8.3,
                    '06': 8.3,
                    '08': 8.3
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.040,
                    '06': 0.030,
                    '08': 0.020
                },
            },
        },
    },
    'PETG-CF': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 270,
                'unload_temp': 270,
                'clean_nozzle_temp': 205,
                'is_soft': False,
                'flow_temp': 255,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.03,
                    '06': 0.02,
                    '08': 0.01
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.78,
                    '06': 4.78,
                    '08': 4.78
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0.003,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'PETG-HF': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 270,
                'unload_temp': 270,
                'clean_nozzle_temp': 170,
                'is_soft': False,
                'flow_temp': 220,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.02,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 6.65,
                    '06': 6.65,
                    '08': 6.65
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.030,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.250,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'ABS': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 280,
                'unload_temp': 280,
                'clean_nozzle_temp': 220,
                'is_soft': False,
                'flow_temp': 270,
                'flow_k': {
                    '02': 0.200,
                    '04': 0.020,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 6.24,
                    '06': 6.24,
                    '08': 6.24
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'ASA': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 280,
                'unload_temp': 280,
                'clean_nozzle_temp': 210,
                'is_soft': False,
                'flow_temp': 260,
                'flow_k': {
                    '02': 0.200,
                    '04': 0.020,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.99,
                    '06': 4.99,
                    '08': 4.99
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'PA': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 280,
                'unload_temp': 280,
                'clean_nozzle_temp': 210,
                'is_soft': False,
                'flow_temp': 260,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.02,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 4.99,
                    '06': 4.99,
                    '08': 4.99
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.7,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'PA-CF': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 300,
                'unload_temp': 300,
                'clean_nozzle_temp': 240,
                'is_soft': False,
                'flow_temp': 290,
                'flow_k': {
                    '02': 0.12,
                    '04': 0.015,
                    '06': 0.008,
                    '08': 0.001
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 3.33,
                    '06': 3.33,
                    '08': 3.33
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.8,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'PA6-CF': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 300,
                'unload_temp': 300,
                'clean_nozzle_temp': 240,
                'is_soft': False,
                'flow_temp': 290,
                'flow_k': {
                    '02': 0.12,
                    '04': 0.015,
                    '06': 0.008,
                    '08': 0.001
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 3.33,
                    '06': 3.33,
                    '08': 3.33
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.8,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'PA-GF': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 300,
                'unload_temp': 300,
                'clean_nozzle_temp': 240,
                'is_soft': False,
                'flow_temp': 290,
                'flow_k': {
                    '02': 0.12,
                    '04': 0.015,
                    '06': 0.008,
                    '08': 0.001
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 3.33,
                    '06': 3.33,
                    '08': 3.33
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.8,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'PA6-GF': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 300,
                'unload_temp': 300,
                'clean_nozzle_temp': 240,
                'is_soft': False,
                'flow_temp': 290,
                'flow_k': {
                    '02': 0.12,
                    '04': 0.015,
                    '06': 0.008,
                    '08': 0.001
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 3.33,
                    '06': 3.33,
                    '08': 3.33
                },
                'flow_accel': {
                    '02': 41.3,
                    '04': 156.8,
                    '06': 346.5,
                    '08': 610.5
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'PC': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 300,
                'unload_temp': 300,
                'clean_nozzle_temp': 220,
                'is_soft': False,
                'flow_temp': 280,
                'flow_k': {
                    '02': 0.20,
                    '04': 0.020,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 6.65,
                    '06': 6.65,
                    '08': 6.65
                },
                'flow_accel': {
                    '02': 38.8,
                    '04': 147.4,
                    '06': 325.7,
                    '08': 573.8
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'PC-ABS': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 280,
                'unload_temp': 280,
                'clean_nozzle_temp': 220,
                'is_soft': False,
                'flow_temp': 270,
                'flow_k': {
                    '02': 0.200,
                    '04': 0.020,
                    '06': 0.012,
                    '08': 0.008
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 6.24,
                    '06': 6.24,
                    '08': 6.24
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.065,
                    '06': 0.045,
                    '08': 0.030
                },
            },
        },
    },
    'PVA': {
        'vendor_generic': {
            'sub_generic': {
                'load_temp': 250,
                'unload_temp': 250,
                'clean_nozzle_temp': 170,
                'is_soft': True,
                'flow_temp': 220,
                'flow_k': {
                    '02': 0.200,
                    '04': 0.030,
                    '06': 0.020,
                    '08': 0.010
                },
                'flow_slow_v': {
                    '02': 0.17,
                    '04': 0.63,
                    '06': 1.386,
                    '08': 2.44
                },
                'flow_fast_v': {
                    '02': 0.83,
                    '04': 6.65,
                    '06': 6.65,
                    '08': 6.65
                },
                'flow_accel': {
                    '02': 39.2,
                    '04': 148.9,
                    '06': 329.2,
                    '08': 579.9
                },
                'flow_k_min': {
                    '02': 0.008,
                    '04': 0.005,
                    '06': 0,
                    '08': 0
                },
                'flow_k_max': {
                    '02': 0.300,
                    '04': 0.100,
                    '06': 0.065,
                    '08': 0.040
                },
            },
        },
    }
}

FILAMENT_PARA_CFG_UNKNOWN = {
    'load_temp': FILAMENT_LOAD_TEMP_UNKNOWN,
    'unload_temp': FILAMENT_UNLOAD_TEMP_UNKNOWN,
    'clean_nozzle_temp': FILAMENT_CLEAN_NOZZLE_TEMP_UNKNOWN,
    'is_soft': FILAMENT_IS_SOFT_UNKNOWN,
    'flow_temp': FILAMENT_FLOW_TEMP_UNKNOWN,
    'flow_k': {
        '02': FILAMENT_FLOW_K_UNKNOWN_02,
        '04': FILAMENT_FLOW_K_UNKNOWN_04,
        '06': FILAMENT_FLOW_K_UNKNOWN_06,
        '08': FILAMENT_FLOW_K_UNKNOWN_08
    },
    'flow_slow_v': {
        '02': FILAMENT_FLOW_SLOW_V_UNKNOWN_02,
        '04': FILAMENT_FLOW_SLOW_V_UNKNOWN_04,
        '06': FILAMENT_FLOW_SLOW_V_UNKNOWN_06,
        '08': FILAMENT_FLOW_SLOW_V_UNKNOWN_08
    },
    'flow_fast_v': {
        '02': FILAMENT_FLOW_FAST_V_UNKNOWN_02,
        '04': FILAMENT_FLOW_FAST_V_UNKNOWN_04,
        '06': FILAMENT_FLOW_FAST_V_UNKNOWN_06,
        '08': FILAMENT_FLOW_FAST_V_UNKNOWN_08
    },
    'flow_accel': {
        '02': FILAMENT_FLOW_ACCEL_UNKNOWN_02,
        '04': FILAMENT_FLOW_ACCEL_UNKNOWN_04,
        '06': FILAMENT_FLOW_ACCEL_UNKNOWN_06,
        '08': FILAMENT_FLOW_ACCEL_UNKNOWN_08
    },
    'flow_k_min': FILAMENT_FLOW_K_MIN_UNKNOWN,
    'flow_k_max': FILAMENT_FLOW_K_MAX_UNKNOWN,
}

class FilamentParameters:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        config_dir = self.printer.get_snapmaker_config_dir()
        config_name = FILAMENT_PARA_CFG_FILE
        self._config_path = os.path.join(config_dir, config_name)
        self._config = self.printer.load_snapmaker_config_file(
                            self._config_path,
                            FILAMENT_PARA_CFG_DEFAULT,
                            create_if_not_exist=True)

        gcode = self.printer.lookup_object('gcode')
        gcode.register_command('FILAMENT_PARA_GET_ALL_INFO',
                               self.cmd_FILAMENT_PARA_GET_ALL_INFO)
        self.printer.register_event_handler("klippy:ready", self._ready)

    def _ready(self):
        version = self._config.get('version', None)
        if version != FILAMENT_PARAMETER_VERSION:
            self.reset_parameters()

    def _nozzle_diameter_to_string(self, nozzle_diameter):
        if nozzle_diameter > 0.1999 and nozzle_diameter < 0.2001:
            return '02'
        elif nozzle_diameter > 0.3999 and nozzle_diameter < 0.4001:
            return '04'
        elif nozzle_diameter > 0.5999 and nozzle_diameter < 0.6001:
            return '06'
        elif nozzle_diameter > 0.7999 and nozzle_diameter < 0.8001:
            return '08'
        else:
            return None

    def get_status(self, eventtime=None):
        return {}

    def get_filaments_max_flow_k(self, soft=False):
        if soft:
            return self._config.get('soft_filaments_max_flow_k', 1.0)
        else:
            return self._config.get('hard_filaments_max_flow_k', 1.0)

    def get_filament_parameters(self, filament_vendor, filament_main_type, filament_sub_type):
        main_type = None
        vendor = None
        sub_type = None
        try:
            main_type = self._config.get(filament_main_type)
            vendor = main_type.get('vendor_' + filament_vendor, None)
            if vendor == None:
                vendor = main_type.get('vendor_generic')
            sub_type = vendor.get('sub_' + filament_sub_type, None)
            if sub_type == None:
                sub_type = vendor.get('sub_generic')
        except:
            pass

        if main_type == None or vendor == None or sub_type == None:
            return FILAMENT_PARA_CFG_UNKNOWN
        else:
            return sub_type
    def get_load_temp(self, filament_vendor, filament_main_type, filament_sub_type):
        parameter = self.get_filament_parameters(filament_vendor, filament_main_type, filament_sub_type)
        return parameter.get('load_temp', FILAMENT_LOAD_TEMP_UNKNOWN)

    def get_unload_temp(self, filament_vendor, filament_main_type, filament_sub_type):
        parameter = self.get_filament_parameters(filament_vendor, filament_main_type, filament_sub_type)
        return parameter.get('unload_temp', FILAMENT_UNLOAD_TEMP_UNKNOWN)

    def get_clean_nozzle_temp(self, filament_vendor, filament_main_type, filament_sub_type):
        parameter = self.get_filament_parameters(filament_vendor, filament_main_type, filament_sub_type)
        return parameter.get('clean_nozzle_temp', FILAMENT_CLEAN_NOZZLE_TEMP_UNKNOWN)

    def get_flow_temp(self, filament_vendor, filament_main_type, filament_sub_type):
        parameter = self.get_filament_parameters(filament_vendor, filament_main_type, filament_sub_type)
        return parameter.get('flow_temp', FILAMENT_FLOW_TEMP_UNKNOWN)

    def get_flow_k(self, filament_vendor, filament_main_type, filament_sub_type, nozzle_diameter):
        parameter = self.get_filament_parameters(filament_vendor, filament_main_type, filament_sub_type)
        nozzle_diameter_str = self._nozzle_diameter_to_string(nozzle_diameter)
        flow_k = parameter.get('flow_k', None)

        if parameter == None or nozzle_diameter_str == None or flow_k == None:
            return FILAMENT_FLOW_K_UNKNOWN
        else:
            return flow_k.get(nozzle_diameter_str, FILAMENT_FLOW_K_UNKNOWN)

    def get_flow_calibrate_parameters(self, filament_vendor, filament_main_type, filament_sub_type, nozzle_diameter):
        flow_temp_val = FILAMENT_FLOW_TEMP_UNKNOWN
        flow_slow_v_val = FILAMENT_FLOW_SLOW_V_UNKNOWN
        flow_fast_v_val = FILAMENT_FLOW_FAST_V_UNKNOWN
        flow_accel_val = FILAMENT_FLOW_ACCEL_UNKNOWN
        flow_k_min_val = FILAMENT_FLOW_K_MIN_UNKNOWN
        flow_k_max_val = FILAMENT_FLOW_K_MAX_UNKNOWN
        flow_k_val = FILAMENT_FLOW_K_UNKNOWN
        try:
            nozzle_diameter_str = self._nozzle_diameter_to_string(nozzle_diameter)
            parameter = self.get_filament_parameters(filament_vendor, filament_main_type, filament_sub_type)
            flow_slow_v = parameter.get('flow_slow_v')
            flow_fast_v = parameter.get('flow_fast_v')
            flow_accel = parameter.get('flow_accel')
            flow_k = parameter.get('flow_k')
            flow_k_min = parameter.get('flow_k_min')
            flow_k_max = parameter.get('flow_k_max')
            flow_temp_val = parameter.get('flow_temp')
            flow_k_min_val = flow_k_min.get(nozzle_diameter_str)
            flow_k_max_val = flow_k_max.get(nozzle_diameter_str)
            flow_k_val = flow_k.get(nozzle_diameter_str)
            flow_slow_v_val = flow_slow_v.get(nozzle_diameter_str)
            flow_fast_v_val = flow_fast_v.get(nozzle_diameter_str)
            flow_accel_val = flow_accel.get(nozzle_diameter_str)

        except:
            flow_temp_val = FILAMENT_FLOW_TEMP_UNKNOWN
            flow_slow_v_val = FILAMENT_FLOW_SLOW_V_UNKNOWN
            flow_fast_v_val = FILAMENT_FLOW_FAST_V_UNKNOWN
            flow_accel_val = FILAMENT_FLOW_ACCEL_UNKNOWN
            flow_k_min_val = FILAMENT_FLOW_K_MIN_UNKNOWN
            flow_k_max_val = FILAMENT_FLOW_K_MAX_UNKNOWN
            flow_k_val = FILAMENT_FLOW_K_UNKNOWN

        finally:
            ret = {
                'temp': flow_temp_val,
                'slow_v': flow_slow_v_val,
                'fast_v': flow_fast_v_val,
                'accel': flow_accel_val,
                'k': flow_k_val,
                'k_min': flow_k_min_val,
                'k_max': flow_k_max_val
            }
            return ret

    def is_allow_to_flow_calibrate(self, filament_vendor, filament_main_type, filament_sub_type, nozzle_diameter):
        is_allow = True
        try:
            if nozzle_diameter > 0.1999 and nozzle_diameter < 0.2001:
                if filament_main_type in NOT_ALLOW_TO_FLOW_CALIBRATE_02:
                    value = NOT_ALLOW_TO_FLOW_CALIBRATE_02.get(filament_main_type)
                    if '*' in value:
                        is_allow = False
                    else:
                        if filament_sub_type in value:
                            is_allow = False
                if filament_main_type.startswith('PA') or filament_main_type.startswith('PC') or \
                    '-CF' in filament_main_type or '-GF' in filament_main_type:
                    is_allow = False
        except:
            is_allow = False

        return is_allow

    def get_is_soft(self, filament_vendor, filament_main_type, filament_sub_type):
        parameter = self.get_filament_parameters(filament_vendor, filament_main_type, filament_sub_type)
        return parameter.get('is_soft', FILAMENT_IS_SOFT_UNKNOWN)

    def reset_parameters(self):
        self._config = copy.deepcopy(FILAMENT_PARA_CFG_DEFAULT)
        self._config['version'] = FILAMENT_PARAMETER_VERSION
        self.printer.update_snapmaker_config_file(self._config_path, self._config, FILAMENT_PARA_CFG_DEFAULT)
        logging.info("[filament_parameters] reset filament parameters")

    def cmd_FILAMENT_PARA_GET_ALL_INFO(self, gcmd):
        gcmd.respond_info(str(self._config))

def load_config(config):
    return FilamentParameters(config)

