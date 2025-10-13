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
    - from: "06:00:00"
      to: "20:00:00"
  {% endfor %}
