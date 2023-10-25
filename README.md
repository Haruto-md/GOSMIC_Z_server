# GOSMIC_Z_server

$cert = New-SelfSignedCertificate -DnsName "localhost" -CertStoreLocation "cert:\LocalMachine\My" -FriendlyName "MyCertificate" -NotAfter (Get-Date).AddYears(10)

$certPath = "C:\path\to\certificate.crt"
Export-Certificate -Cert $cert -FilePath $certPath

$keyPath = "C:\path\to\privatekey.key"
Export-PfxCertificate -Cert $cert -FilePath $keyPath -Password (Read-Host -Prompt "Enter password" -AsSecureString) 
