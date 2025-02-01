{% for sensor in leak_sensors %}
### {{ sensor.name }} ###
- alias: "{{ sensor.name }} leak sensor: activate"
  mode: single
  trigger:
    - platform: state
      entity_id: "{{ sensor.entity }}"
      from: "off"
      to: "on"
  action:
    - service: notify.dan
      data:
        message: "Leak detected in {{ sensor.name }}"
        title: "Leak detected"
        data:
          notification_icon: "mdi:water"
          channel: "leak-{{ sensor.name }}"

- alias: "{{ sensor.name }} leak sensor: deactivate"
  mode: single
  trigger:
    - platform: state
      entity_id: "{{ sensor.entity }}"
      from: "on"
      to: "off"
  action:
    - service: notify.dan
      data:
        message: "Leak resolved in {{ sensor.name }}"
        title: "Leak resolved"
        data:
          notification_icon: "mdi:water"
          channel: "leak-{{ sensor.name }}"
{% endfor %}
