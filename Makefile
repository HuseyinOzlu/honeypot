.PHONY: build run stop clean logs

# Projeyi tek tuşla tamamen ayağa kaldırır
run:
	docker-compose up --build -d
	@echo "Honeypot Basariyla Baslatildi! SSH ile port 2222'ye baglanabilirsiniz."

# Projeyi durdurur
stop:
	docker-compose down

# Logları izler
logs:
	docker-compose logs -f

# Bütün her şeyi (imajlar ve veritabanı dahil) silip temizler
clean:
	docker-compose down -v --rmi all
