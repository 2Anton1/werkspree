<?php
declare(strict_types=1);

/**
 * Klarraum Gesundheit: datensparsame Workshop-Anfrage.
 * Vor der Veröffentlichung nur auf einem HTTPS-fähigen eigenen Server einsetzen.
 */
session_name('klarraum_anfrage');
session_set_cookie_params(['httponly' => true, 'secure' => true, 'samesite' => 'Lax']);
session_start();

if (!isset($_SESSION['csrf'])) {
    $_SESSION['csrf'] = bin2hex(random_bytes(32));
}

function clean(string $value, int $limit): string
{
    $shortened = function_exists('mb_substr') ? mb_substr($value, 0, $limit) : substr($value, 0, $limit);
    return trim($shortened);
}

function escape(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

$error = '';
$sent = false;
$values = ['organisation' => '', 'name' => '', 'email' => '', 'phone' => '', 'team' => '', 'message' => ''];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    foreach ($values as $key => $_) {
        $values[$key] = clean((string) ($_POST[$key] ?? ''), $key === 'message' ? 1600 : 180);
    }
    $token = (string) ($_POST['csrf'] ?? '');
    $honeypot = trim((string) ($_POST['website'] ?? ''));
    $confirmed = isset($_POST['no_sensitive_data']);

    if ($honeypot !== '') {
        $sent = true;
    } elseif (!hash_equals($_SESSION['csrf'], $token)) {
        $error = 'Die Sitzung ist abgelaufen. Bitte laden Sie die Seite neu und versuchen Sie es erneut.';
    } elseif ($values['organisation'] === '' || $values['name'] === '' || !filter_var($values['email'], FILTER_VALIDATE_EMAIL) || !$confirmed) {
        $error = 'Bitte füllen Sie Organisation, Name und eine gültige E-Mail-Adresse aus und bestätigen Sie den Hinweis zu sensiblen Daten.';
    } else {
        $subject = 'Workshop-Anfrage über klarraum-gesundheit.de';
        $message = "Organisation: {$values['organisation']}\nName: {$values['name']}\nE-Mail: {$values['email']}\nTelefon: {$values['phone']}\nTeamgröße: {$values['team']}\n\nNachricht:\n{$values['message']}";
        $headers = [
            'From: Klarraum Gesundheit <kontakt@klarraum-gesundheit.de>',
            'Reply-To: ' . $values['email'],
            'Content-Type: text/plain; charset=UTF-8',
        ];
        $sent = mail('kontakt@klarraum-gesundheit.de', $subject, $message, implode("\r\n", $headers));
        if (!$sent) {
            $error = 'Die Nachricht konnte gerade nicht versendet werden. Bitte schreiben Sie direkt an kontakt@klarraum-gesundheit.de.';
        } else {
            $_SESSION['csrf'] = bin2hex(random_bytes(32));
            $values = array_fill_keys(array_keys($values), '');
        }
    }
}
?>
<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <title>Workshop anfragen · Klarraum Gesundheit</title>
    <link rel="icon" href="assets/logo-signal.svg" type="image/svg+xml">
    <link rel="stylesheet" href="assets/legal.css">
  </head>
  <body>
    <header class="topbar"><div class="shell"><a class="brand" href="index.html"><img src="assets/logo-signal.svg" alt=""><span><span class="accent">Klarraum</span> Gesundheit</span></a><a class="back" href="index.html">Zur Startseite</a></div></header>
    <main><article class="shell"><p class="eyebrow">Unverbindlich</p><h1>Workshop anfragen</h1><p class="intro">Erzählen Sie kurz, für welches Team Sie einen Workshop planen. Wir melden uns persönlich zurück.</p><?php if ($sent): ?><div class="notice"><strong>Vielen Dank.</strong><br>Ihre Anfrage wurde versendet. Wir melden uns zeitnah bei Ihnen.</div><?php elseif ($error !== ''): ?><div class="notice error" role="alert"><?= escape($error) ?></div><?php endif; ?><form method="post" action="anfrage.php" novalidate><input type="hidden" name="csrf" value="<?= escape($_SESSION['csrf']) ?>"><div class="hp" aria-hidden="true"><label>Website <input type="text" name="website" tabindex="-1" autocomplete="off"></label></div><div class="form-grid"><label class="field">Organisation *<input name="organisation" required maxlength="180" autocomplete="organization" value="<?= escape($values['organisation']) ?>"></label><label class="field">Ihr Name *<input name="name" required maxlength="180" autocomplete="name" value="<?= escape($values['name']) ?>"></label><label class="field">Geschäftliche E-Mail-Adresse *<input type="email" name="email" required maxlength="180" autocomplete="email" value="<?= escape($values['email']) ?>"></label><label class="field">Telefon <input type="tel" name="phone" maxlength="180" autocomplete="tel" value="<?= escape($values['phone']) ?>"></label><label class="field">Ungefähre Teamgröße <select name="team"><option value="">Bitte auswählen</option><?php foreach (['bis 10 Personen', '11 bis 25 Personen', '26 bis 50 Personen', 'mehr als 50 Personen'] as $option): ?><option<?= $values['team'] === $option ? ' selected' : '' ?>><?= escape($option) ?></option><?php endforeach; ?></select></label><label class="field full">Worum geht es? <textarea name="message" maxlength="1600" placeholder="Zum Beispiel: gewünschter Zeitraum oder organisatorische Frage. Bitte keine Patienten- oder Gesundheitsdaten eingeben."><?= escape($values['message']) ?></textarea></label></div><label class="check"><input type="checkbox" name="no_sensitive_data" value="1" required> <span>Ich bestätige, dass meine Anfrage keine Patienten-, Gesundheits- oder sonstigen sensiblen Daten enthält. Die <a href="datenschutz.html">Datenschutzhinweise</a> habe ich gelesen.</span></label><button class="button" type="submit">Anfrage senden</button></form></article></main>
    <footer><div class="shell"><p><a href="index.html">Startseite</a> · <a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></p></div></footer>
  </body>
</html>
