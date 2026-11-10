# CNPJ monitor log

## 2026-11-10 ~UTC CHANGE
- Situação cadastral: ATIVA (was INAPTA) per Minhas Dívidas e Pendências
- Pendências open: no cadastral pendência or omission shown. Receita analysis banner says 'Análise incompleta' (could not reach all RFB/PGFN data; Atualizar did not clear it), so not yet final.
- Fines: 70 items under Lançamento de Ofício, all 'A vencer', due 08/12/2026: 69 x R$50,00 (4406-01) + 1 x R$100,00 (5440-01, period 17/11/2021) = R$3.550,00 total. No separate DEFIS fine seen.
- Installment availability: not checked (guessed parcelamentos URL returned not found); fines still a vencer
- Not checked this run: DCTFWeb list, public CNPJ consulta, Pagamentos e Parcelamentos DARF issuance
- Actions taken: Rodo logged in and solved captcha on Pendências page; read both pages of fines; pushed status-change notice
- Captcha encountered: Y (Pendências page, solved by Rodo); login required: Y

## 2026-11-09 ~20:30 UTC NEEDS-RODO
- Situação cadastral: not checked (blocked by login)
- Pendências open: not checked; last known: cadastral pendência open, omissions cleared, 68 x R$50,00 = R$3.400,00 fines (4406-01) due 08/12/2026, a vencer
- Fines/totals: not re-checked
- Installment availability: not checked
- Actions taken: e-CAC session expired (gov.br login page); pushed Rodo to log in; re-checked ~8 times over ~30 min, login never completed; stopped
- Captcha encountered: N (login required: Y)

## 2026-11-09 18:51 UTC NEEDS-RODO
- Situação cadastral: not checked (blocked by login)
- Pendências open: not checked; last known (03:30 UTC run): cadastral pendência open, omissions cleared, 68 x R$50,00 = R$3.400,00 fines (4406-01) due 08/12/2026, a vencer
- Fines/totals: not re-checked
- Installment availability: not checked
- Actions taken: e-CAC session expired (gov.br login page); pushed Rodo to log in; re-checked every ~2 min for ~30 min, login never completed; stopped
- Captcha encountered: N (login required: Y)

## 2026-11-09 03:30 UTC CHANGE
- Situação cadastral: INAPTA since 26/02/2021 (still)
- Pendências open: cadastral 'Inscrição inapta - omissão de declarações' still open. 'Declaração Não Entregue' (omissions) item is GONE after refresh = omissions cleared.
- Fines: 68 x R$50,00 = R$3.400,00, all code 4406-01 (PGDAS-D MAED), due 08/12/2026, status 'A vencer'. No DEFIS or DCTFWeb 5440-01 fines listed yet.
- Installment availability: not checked this run (fines still a vencer)
- Not checked this run: DCTFWeb list, public CNPJ consulta, Pagamentos e Parcelamentos
- Actions taken: session had expired; Rodo logged in after push; switched to CNPJ representation; refreshed analysis
- Captcha encountered: N (login required: Y)

## 2026-11-08 NEEDS-RODO
- Situação cadastral: not checked (blocked)
- Pendências open: not checked — Minhas Dívidas e Pendências showed a captcha; session itself appears logged in (Representante no CNPJ)
- Fines/totals: not checked
- Installment availability: not checked
- Actions taken: none; push notification sent asking Rodo to solve captcha
- Captcha encountered: Y
