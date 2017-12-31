from Crypto.PublicKey import RSA

private1 = RSA.generate(2048)
public1 = private1.publickey().exportKey('DER').hex()
private2 = RSA.generate(2048)
public2 = private2.publickey().exportKey('DER').hex()
private3 = RSA.generate(2048)
public3 = private3.publickey().exportKey('DER').hex()