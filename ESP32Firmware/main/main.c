#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include "esp_bt.h"
#include "esp_gap_ble_api.h"
#include "esp_log.h"
#include "nvs_flash.h"      // For NVS functions like nvs_flash_init
#include "esp_bt_main.h"   // For esp_bluedroid_* functions
#include "esp_err.h"        // For error handling

#define TAG "ESP_FMDN"

// This is the advertisement key / EID. Change it to your own EID.
const char *eid_string = "INSERT_YOUR_ADVERTISEMENT_KEY_HERE";

// Function to convert a hex string into a byte array
void hex_string_to_bytes(const char *hex, uint8_t *bytes, size_t len) {
    for (size_t i = 0; i < len; i++) {
        sscanf(hex + 2 * i, "%2hhx", &bytes[i]);
    }
}

void app_main() {
    // Initialize NVS (required for BLE initialization)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // Initialize Bluetooth controller
    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_bt_controller_init(&bt_cfg));
    ESP_ERROR_CHECK(esp_bt_controller_enable(ESP_BT_MODE_BLE));

    // Initialize Bluedroid stack
    ESP_ERROR_CHECK(esp_bluedroid_init());
    ESP_ERROR_CHECK(esp_bluedroid_enable());

    // Set BLE TX power to 9 dBm
    ESP_ERROR_CHECK(esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_DEFAULT, ESP_PWR_LVL_P9));
    ESP_ERROR_CHECK(esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_ADV, ESP_PWR_LVL_P9));
    ESP_LOGI(TAG, "Set BLE TX Power to 9 dBm");

    // NOTE: BLE MAC address can be anything
    // FMDN frame supporting a 160-bit curve.
    // details https://developers.google.com/nearby/fast-pair/specifications/extensions/fmdn#advertised-frames
    uint8_t adv_raw_data[1+2 + 1+25] = {
        0x02, // 0 Length
        0x01, // 1 Flags data type value
        0x06, // 2 Flags data

        // Service Data
        0x19, // 3 Length 25bytes
        0x16, // 4 Service data data type value
        0xAA, // 5 16-bit service UUID
        0xFE, // 6 type
        0x41, // 7 FMDN frame type with unwanted tracking protection mode indication

        // 8-27 20-byte tacking field EID (ephemeral identifier)
        // byte pattern can be simply swapped in binary
        0x56,0x57,0x58,0x59,0x5A,0x5B,0x5C,0x5D,0x5E,0x5F,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,

        0x01, // 28 Hashed flags
        /* The hashed flags field is calculated as follows (bits are referenced from most significant to least significant):
          Bits 0-4: Reserved (set to zeros).
          Bits 5-6 indicates the battery level for the device as follows:
            00: Battery level indication unsupported
            01: Normal battery level
            10: Low battery level
            11: Critically low battery level (battery replacement needed soon)
          Bit 7 is set to 1 if the beacon is in unwanted tracking protection mode, and 0 otherwise
        */
    };

    /* string based EID injection used */
    if(eid_string[0] != 'I')
    {
      uint8_t eid_bytes[20];
      hex_string_to_bytes(eid_string, eid_bytes, 20);
      memcpy(&adv_raw_data[8], eid_bytes, 20);
    }

    ESP_ERROR_CHECK(esp_ble_gap_config_adv_data_raw(adv_raw_data, sizeof(adv_raw_data)));

    // Configure advertisement parameters
    esp_ble_adv_params_t adv_params = {

        // change those if you want to save power
        .adv_int_min = 0x20,
        .adv_int_max = 0x20,

        .adv_type = ADV_TYPE_NONCONN_IND,
        .own_addr_type = BLE_ADDR_TYPE_PUBLIC,
        .channel_map = ADV_CHNL_ALL,
        .adv_filter_policy = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,
    };

    // Start advertising
    ESP_ERROR_CHECK(esp_ble_gap_start_advertising(&adv_params));
    ESP_LOGI(TAG, "BLE advertising started.");
}