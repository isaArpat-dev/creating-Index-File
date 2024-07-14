import os
import hashlib
import time
import random
import matplotlib.pyplot as plt
# Klasör yolları
base_dir = os.path.dirname(os.path.abspath(__file__))
index_dir = os.path.join(base_dir, '..', 'Index')
processed_dir = os.path.join(base_dir, '..', 'Processed')
unprocessed_passwords_dir = os.path.join(base_dir, '..', 'Unprocessed-Passwords')

performance_measurements = []

def list_files(directory):
    """Belirtilen klasördeki dosyaları listele."""
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def create_hashes(password):
    """Verilen parolanın MD5, SHA-128 ve SHA-256 hash değerlerini döndürür."""
    md5 = hashlib.md5(password.encode()).hexdigest()
    sha128 = hashlib.sha1(password.encode()).hexdigest()[:32]  # SHA-1 kullanarak SHA-128 benzeri hash
    sha256 = hashlib.sha256(password.encode()).hexdigest()
    return md5, sha128, sha256

def is_valid_dirname(char):
    """Klasör ismi olarak geçerli bir karakter olup olmadığını kontrol eder."""
    invalid_chars = r'\/:*?"<>|'
    return char not in invalid_chars

def load_existing_passwords():
    """Index klasöründeki mevcut parolaları bir set içinde tutar."""
    existing_passwords = set()
    
    for root, dirs, files in os.walk(index_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            with open(file_path, 'r') as file:
                for line in file:
                    existing_passwords.add(line.strip())
                    
    return existing_passwords

def process_passwords():
    """Unprocessed-Passwords klasöründeki dosyaları okuyup parolaları işler."""
    processed_passwords = set()  # Tekrarlardan kaçınmak için
    existing_passwords = load_existing_passwords()  # Mevcut parolaları yükle
    unprocessed_files = list_files(unprocessed_passwords_dir)
    
    for file_name in unprocessed_files:
        file_path = os.path.join(unprocessed_passwords_dir, file_name)
        with open(file_path, 'r') as file:
            for line in file:
                password = line.strip()
                if not password or password in processed_passwords or password in existing_passwords:
                    continue  # Zaten işlenmiş, mevcut veya boş parola
                processed_passwords.add(password)
                existing_passwords.add(password)  # Mevcut parolalar setine ekle
                
                # İşlenmiş veriyi oluştur
                md5, sha128, sha256 = create_hashes(password)
                processed_content = f"{password}|{md5}|{sha128}|{sha256}|{file_name}\n"
                
                # İşlenmiş veriyi Processed klasörüne kaydet
                processed_file_path = os.path.join(processed_dir, f"{file_name}_processed.txt")
                with open(processed_file_path, 'a') as processed_file:
                    processed_file.write(processed_content)
                
                # Parolanın indekslenmesi
                first_char = password[0].lower()
                if not is_valid_dirname(first_char):
                    first_char = 'other'
                target_dir = os.path.join(index_dir, first_char)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                
                index_files = list_files(target_dir)
                index_file_path = os.path.join(target_dir, f'index_0.txt')
                
                if index_files:
                    index_file_path = os.path.join(target_dir, f'index_{len(index_files) - 1}.txt')
                    with open(index_file_path, 'r') as index_file:
                        lines = index_file.readlines()
                    if len(lines) >= 10000:
                        index_file_path = os.path.join(target_dir, f'index_{len(index_files)}.txt')
                
                with open(index_file_path, 'a') as index_file:
                    index_file.write(f"{password}\n")
        
        # İşlenmiş dosyayı Unprocessed klasöründen kaldır
        os.remove(file_path)
        print(f"{file_name} dosyası işlendi ve Processed klasörüne kaydedildi.")
    
    return processed_passwords  # İşlenmiş parolaları döndür

def search_password(query):
    """Verilen parolayı index klasöründe arar."""
    first_char = query[0].lower()
    if not is_valid_dirname(first_char):
        first_char = 'other'
    target_dir = os.path.join(index_dir, first_char)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    index_files = list_files(target_dir)
    found = False

    for index_file in index_files:
        index_file_path = os.path.join(target_dir, index_file)
        with open(index_file_path, 'r') as file:
            for line in file:
                if line.strip() == query:
                    # İşlenmiş şifre verisini Processed klasöründen oku
                    processed_files = list_files(processed_dir)
                    for processed_file in processed_files:
                        processed_file_path = os.path.join(processed_dir, processed_file)
                        with open(processed_file_path, 'r') as p_file:
                            for p_line in p_file:
                                if p_line.startswith(query):
                                    return f"Parola bulundu: {p_line.strip()}"
                    found = True
                    break
        if found:
            break

    if not found:
        # Parola bulunamazsa hem Index hem de Processed klasörlerine kaydet
        md5, sha128, sha256 = create_hashes(query)
        processed_content = f"{query}|{md5}|{sha128}|{sha256}|search\n"

        # Index klasörüne kaydet
        index_file_path = os.path.join(target_dir, f'index_{len(index_files)}.txt')
        with open(index_file_path, 'a') as index_file:
            index_file.write(f"{query}\n")

        # Processed klasörüne kaydet
        processed_file_path = os.path.join(processed_dir, 'search_processed.txt')
        with open(processed_file_path, 'a') as processed_file:
            processed_file.write(processed_content)

        return f"Parola '{query}' bulunamadı, arama kaydedildi."

    return f"Parola '{query}' bulunamadı."

def measure_search_performance():
    """10 rastgele parolanın arama sürelerini ölç ve ortalamasını al."""
    existing_passwords = load_existing_passwords()  # Mevcut parolaları yükle
    if len(existing_passwords) < 10:
        print("Yeterli sayıda parola yok.")
        return
    
    sample_passwords = random.sample(existing_passwords, 10)
    performance_measurements = []

    for i, password in enumerate(sample_passwords, 1):
        start_time = time.time()
        search_password(password)
        end_time = time.time()
        search_time = end_time - start_time
        performance_measurements.append((i, search_time))
    
    # Grafik oluşturma
    plt.figure(figsize=(10, 5))
    plt.plot([x[0] for x in performance_measurements], [x[1] for x in performance_measurements], marker='o')
    plt.title('Arama Performansı')
    plt.xlabel('Arama Numarası')
    plt.ylabel('Arama Süresi (saniye)')
    plt.xticks(range(1, 11))
    plt.grid(True)
    plt.show()



if __name__ == "__main__":
    while True:
        print("\n1. Parolaları İşle")
        print("2. Parola Ara")
        print("3. Arama Performansını Ölç")
        print("4. Çıkış")
        choice = input("Bir seçenek girin: ").strip()
        
        if choice == '1':
            process_passwords()
        elif choice == '2':
            query = input("Aramak istediğiniz parolayı girin: ").strip()
            if query:
                result = search_password(query)
                print(result)
        elif choice == '3':
            measure_search_performance()
        elif choice == '4':
            break
        else:
            print("Geçersiz seçenek. Lütfen tekrar deneyin.")