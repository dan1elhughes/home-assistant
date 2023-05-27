{% set daysOfTheWeek = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday"
] -%}

heating:
  name: "Heating"
  icon: mdi:thermometer-auto
  {% for day in daysOfTheWeek %}
  {{ day }}:
    - from: "07:00:00"
      to: "22:00:00"
  {% endfor %}

offpeak:
  name: "Off-peak"
  icon: mdi:transmission-tower
  {% for day in daysOfTheWeek %}
  {{ day }}:
    - from: "01:00:00"
      to: "08:00:00"
  {% endfor %}
