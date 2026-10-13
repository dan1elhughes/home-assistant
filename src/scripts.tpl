# https://tasmota.github.io/docs/Device-Recovery/#fast-power-cycle-device-recovery
tasmota_provide_reset_sequence:
  alias: "Tasmota: Provide reset sequence"
  description: "Provide the reset sequence for a Tasmota device"
  fields:
    device:
      description: "The Tasmota device to provide the reset sequence for"
      example: "switch.tasmota_device"
      required: true
  sequence:
    - repeat:
        count: 6
        sequence:
          - action: switch.turn_on
            target:
              entity_id: "{% raw %}{{ device }}{% endraw %}"
          - delay: "00:00:01"
          - action: switch.turn_off
            target:
              entity_id: "{% raw %}{{ device }}{% endraw %}"
          - delay: "00:00:01"
    - action: switch.turn_on
      target:
        entity_id: "{% raw %}{{ device }}{% endraw %}"

family_alarm:
  alias: "Family alarm"
  description: "Set an alarm on each phone for the time and label picked on the dashboard"
  sequence:
    - repeat:
        for_each:
          {%- for device in devices %}
          {%- if device.family_alarm %}
          - notify.mobile_app_{{ device.prefix | replace('sensor.', '') }}
          {%- endif %}
          {%- endfor %}
        sequence:
          - action: "{% raw %}{{ repeat.item }}{% endraw %}"
            data:
              message: "command_activity"
              data:
                intent_package_name: "com.google.android.deskclock"
                intent_action: "android.intent.action.SET_ALARM"
                intent_extras: >-
                  android.intent.extra.alarm.HOUR:{% raw %}{{ state_attr('input_datetime.family_alarm', 'hour') | int }}{% endraw %},android.intent.extra.alarm.MINUTES:{% raw %}{{ state_attr('input_datetime.family_alarm', 'minute') | int }}{% endraw %},android.intent.extra.alarm.MESSAGE:{% raw %}{{ states('input_text.family_alarm_label') | default('Dinner', true) }}{% endraw %},android.intent.extra.alarm.VIBRATE:true,android.intent.extra.alarm.SKIP_UI:true
                ttl: 0
                priority: high
    - action: input_text.set_value
      target:
        entity_id: input_text.family_alarm_label
      data:
        value: "Dinner"
    - action: input_datetime.set_datetime
      target:
        entity_id: input_datetime.family_alarm
      data:
        time: "19:00:00"

charge_id3:
  alias: "Charge ID3"
  description: >-
    Sets the ID3 charge target to the car's current battery level rounded up to
    the next 5%, sets the auto increment to 10% at 10:00, turns on Octopus smart
    charge, and switches the charger mode to ID3.
  icon: mdi:car
  mode: single
  sequence:
    - alias: "Set the charge target to the current level rounded up to 5%"
      action: number.set_value
      target:
        entity_id: number.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_charge_target
      data:
        value: >-
          {% raw %}{{ [ [((states('sensor.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_state_of_charge') | float(0) / 5) | round(0, 'ceil') * 5) | int, 5] | max, 100] | min }}{% endraw %}
    - alias: "Set the increment to 10%"
      action: input_number.set_value
      target:
        entity_id: input_number.id3_charge_target_increment
      data:
        value: 10
    - alias: "Set the increment time to 10:00"
      action: input_datetime.set_datetime
      target:
        entity_id: input_datetime.id3_charge_target_increment_time
      data:
        time: "10:00:00"
    - alias: "Turn on auto increment"
      action: input_boolean.turn_on
      target:
        entity_id: input_boolean.id3_auto_increment_charge_target
    - alias: "Turn on ID3 smart charge"
      action: switch.turn_on
      target:
        entity_id: switch.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_smart_charge
    - alias: "Set charger mode to ID3"
      action: input_select.select_option
      target:
        entity_id: input_select.charger_mode
      data:
        option: ID3

charge_zoe:
  alias: "Charge Zoe"
  description: >-
    Turns off the ID3 smart charge and auto increment, sets the Zoe charge
    target to 80%, and switches the charger mode to Zoe.
  icon: mdi:car-electric
  mode: single
  sequence:
    - alias: "Turn off ID3 auto increment"
      action: input_boolean.turn_off
      target:
        entity_id: input_boolean.id3_auto_increment_charge_target
    - alias: "Turn off ID3 smart charge"
      action: switch.turn_off
      target:
        entity_id: switch.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_smart_charge
    - alias: "Set the Zoe charge target to 80%"
      action: input_number.set_value
      target:
        entity_id: input_number.zoe_charge_target
      data:
        value: 80
    - alias: "Set charger mode to Zoe"
      action: input_select.select_option
      target:
        entity_id: input_select.charger_mode
      data:
        option: Zoe
