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
