(function () {
  var suspiciousRegex = /(--|;|\/\*|\*\/|\b(select|insert|update|delete|drop|union|xp_)\b)/i;

  function hasSuspiciousPattern(value) {
    return suspiciousRegex.test((value || "").trim());
  }

  function validateForm(event) {
    var form = event.target;
    var fields = form.querySelectorAll("input[data-validate='sql'], textarea[data-validate='sql']");
    for (var i = 0; i < fields.length; i += 1) {
      if (hasSuspiciousPattern(fields[i].value)) {
        alert("Entrada invalida detectada. Remova padroes suspeitos e tente novamente.");
        fields[i].focus();
        event.preventDefault();
        return false;
      }
    }
    return true;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var forms = document.querySelectorAll("form.js-safe-form");
    for (var i = 0; i < forms.length; i += 1) {
      forms[i].addEventListener("submit", validateForm);
    }
  });
})();
