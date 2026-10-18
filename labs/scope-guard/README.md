# scope-guard (savunma)

Lab konteyneri yok. Doğrulayıcı runner'ın kapsam korumasını çalıştırır: oturum ağı dışındaki her hedef
(ev LAN'ı, Docker köprüleri, Tailscale, loopback, alan adları) reddedilmeli; yalnız oturum alt ağı ve
`target-*` / `verifier-*` servis adları kabul edilmeli. Test: tests/test_runner.py.
