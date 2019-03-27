import rsa

(tambe_pub, tambe_priv) = rsa.newkeys(512)
message = 'beautiful Tambe!'.encode('utf8')
encrypted_msg = rsa.encrypt(message, tambe_pub)
message = rsa.decrypt(encrypted_msg, tambe_priv)

def test_encryption_decryption():
	assert message.decode('utf8') == 'beautiful Tambe!'

