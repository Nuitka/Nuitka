import rsa

# nuitka-skip-unless-imports: rsa

(tambe_pub, tambe_priv) = rsa.newkeys(512)
message = 'beautiful Tambe!'.encode('utf8')
encrypted_msg = rsa.encrypt(message, tambe_pub)
message = rsa.decrypt(encrypted_msg, tambe_priv)

def encryption_decryption():
	'''Function to test encryption and decryption'''
	assert message.decode('utf8') == 'beautiful Tambe!'

if __name__ == '__main__':
	encryption_decryption()
