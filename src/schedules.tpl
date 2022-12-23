{% set daysOfTheWeek = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday"
] -%}

offpeak:
  name: "Off-peak"
  icon: mdi:transmission-tower
  {% for day in daysOfTheWeek %}
  {{ day }}:
    - from: "00:30:00"
      to: "07:30:00"
  {% endfor %}

heating:
  name: "Heating"
  icon: mdi:thermometer-auto
  {% for day in daysOfTheWeek %}
  {{ day }}:
    - from: "07:00:00"
      to: "22:00:00"
  {% endfor %}
