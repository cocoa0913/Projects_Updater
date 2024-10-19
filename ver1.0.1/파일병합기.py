import os
import shutil
import re
import tkinter as tk
from tkinter import filedialog, messagebox

# 파일 확장자 필터 (css, jsp, java, html, js, jpg, png)
text_file_extensions = {
    '.css': 'CSS',
    '.jsp': 'JSP',
    '.java': 'JAVA',
    '.html': 'HTML',
    '.js': 'JS'
}
binary_file_extensions = ['.jpg', '.png']

# GUI 경로 선택 기능
def select_folder(prompt):
    folder_selected = filedialog.askdirectory(title=prompt)
    return folder_selected

# 백업 폴더 생성 (프로그램 폴더 내에 생성)
def create_backup_folder():
    backup_folder = os.path.join(os.getcwd(), 'backup')
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    return backup_folder

# 파일의 인코딩을 시도하여 읽기
def read_file_with_encoding(file_path):
    encodings = ['utf-8', 'latin-1', 'cp949']  # 다양한 인코딩을 시도
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.readlines(), encoding  # 파일 내용과 성공한 인코딩 반환
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"{file_path} 파일을 읽을 수 없습니다.")  # 시도한 인코딩들로도 읽지 못할 때

# 특정 구문에서 DB 이름, 사용자명, 비밀번호 변경
def replace_db_credentials(line, db_name=None, db_user=None, db_password=None):
    match = re.search(r'DriverManager\.getConnection\("jdbc:mysql://localhost:3306/(.*?)",\s*"(.*?)",\s*"(.*?)"\);', line)
    
    if match:
        original_db_name = match.group(1)
        original_user = match.group(2)
        original_password = match.group(3)
        
        db_name = db_name if db_name else original_db_name
        db_user = db_user if db_user else original_user
        db_password = db_password if db_password else original_password
        
        return f'Connection conn = DriverManager.getConnection("jdbc:mysql://localhost:3306/{db_name}", "{db_user}", "{db_password}");\n'
    
    return line

# 파일 병합
def merge_files(A_file, B_file, backup_folder, db_name=None, db_user=None, db_password=None):
    try:
        backup_filename = os.path.join(backup_folder, os.path.basename(A_file) + '_backup')
        shutil.copy2(A_file, backup_filename)

        # B 파일을 여러 인코딩으로 시도하여 읽기
        b_lines, encoding_used = read_file_with_encoding(B_file)
        print(f"{B_file} 파일을 {encoding_used} 인코딩으로 읽었습니다.")

        # A 파일 내용 병합
        with open(A_file, 'r+', encoding='utf-8') as f_a:
            modified_lines = [replace_db_credentials(line, db_name, db_user, db_password) for line in b_lines]
            f_a.seek(0)
            f_a.truncate()
            f_a.writelines(modified_lines)

        return True, None
    except Exception as e:
        return False, str(e)

# 파일 복사 및 병합 실행
def copy_or_merge_files(A_folder, B_folder, db_name=None, db_user=None, db_password=None):
    backup_folder = create_backup_folder()
    try:
        for dirpath, _, filenames in os.walk(B_folder):
            # 디렉토리 생성 (폴더는 무조건 복사)
            rel_path = os.path.relpath(dirpath, B_folder)
            dest_folder_path = os.path.join(A_folder, rel_path)
            os.makedirs(dest_folder_path, exist_ok=True)  # 폴더는 항상 복사

            for filename in filenames:
                B_file = os.path.join(dirpath, filename)
                A_file = os.path.join(dest_folder_path, filename)

                ext = os.path.splitext(filename)[1].lower()

                # 사용자 선택에 따라 파일 필터링 (텍스트와 이미지 파일)
                if ext in text_file_extensions and not copy_text_files[ext].get():
                    continue
                if ext in binary_file_extensions and not copy_image_files.get():
                    continue

                # A 폴더에 없는 파일은 복사
                if not os.path.exists(A_file):
                    if ext in binary_file_extensions:
                        shutil.copyfile(B_file, A_file)  # 이미지 파일은 바이너리 모드로 복사
                    else:
                        os.makedirs(os.path.dirname(A_file), exist_ok=True)
                        shutil.copy2(B_file, A_file)
                else:
                    # A와 B에 모두 존재하는 파일은 병합
                    success, error = merge_files(A_file, B_file, backup_folder, db_name, db_user, db_password)
                    if not success:
                        return False, error
        return True, None
    except Exception as e:
        return False, str(e)

# 모든 체크박스를 선택하는 함수
def select_all_checkboxes():
    for var in copy_text_files.values():
        var.set(True)
    copy_image_files.set(True)

# GUI 창 및 경로 지정
def run_gui():
    global copy_text_files, copy_image_files

    root = tk.Tk()
    root.title("폴더 비교 및 병합 프로그램")

    # BooleanVar() 초기화
    copy_text_files = {ext: tk.BooleanVar() for ext in text_file_extensions}
    copy_image_files = tk.BooleanVar()

    def set_A_folder():
        global A_folder
        A_folder = select_folder("기존 폴더를 지정하세요")
        a_folder_label.config(text=f"기존 폴더: {A_folder}")

    def set_B_folder():
        global B_folder
        B_folder = select_folder("수정된 폴더를 지정하세요")
        b_folder_label.config(text=f"수정된 폴더: {B_folder}")

    def db_credentials_input():
        db_popup = tk.Toplevel(root)
        db_popup.title("DB정보 입력")

        tk.Label(db_popup, text="DB이름:").pack(pady=5)
        db_name_entry = tk.Entry(db_popup)
        db_name_entry.pack(pady=5)

        tk.Label(db_popup, text="계정:").pack(pady=5)
        db_user_entry = tk.Entry(db_popup)
        db_user_entry.pack(pady=5)

        tk.Label(db_popup, text="비밀번호:").pack(pady=5)
        db_password_entry = tk.Entry(db_popup, show="*")
        db_password_entry.pack(pady=5)

        def on_submit():
            global db_name, db_user, db_password
            db_name = db_name_entry.get() or None
            db_user = db_user_entry.get() or None
            db_password = db_password_entry.get() or None
            db_popup.destroy()

        tk.Button(db_popup, text="확인", command=on_submit).pack(pady=5)
        tk.Button(db_popup, text="기본값", command=db_popup.destroy).pack(pady=5)

        db_popup.grab_set()
        root.wait_window(db_popup)

    def start_process():
        if A_folder and B_folder:
            db_credentials_input()

            success, error = copy_or_merge_files(A_folder, B_folder, db_name, db_user, db_password)
            if success:
                messagebox.showinfo("성공", "파일 병합이 완료되었습니다.")
            else:
                messagebox.showerror("실패", f"파일 병합 실패: {error}")
        else:
            messagebox.showwarning("경고", "폴더를 지정해 주세요.")

    # Tkinter GUI 구성
    tk.Label(root, text="기존 폴더를 지정하세요:").pack(pady=5)
    a_folder_label = tk.Label(root, text="기존 폴더 경로를 선택해 주세요", fg="gray")
    a_folder_label.pack()
    tk.Button(root, text="기존 폴더 선택", command=set_A_folder).pack(pady=10)

    tk.Label(root, text="수정된 폴더를 지정하세요:").pack(pady=5)
    b_folder_label = tk.Label(root, text="수정된 폴더 경로를 선택해 주세요", fg="gray")
    b_folder_label.pack()
    tk.Button(root, text="수정된 폴더 선택", command=set_B_folder).pack(pady=10)

    # 각 텍스트 파일 타입별 체크박스 추가
    for ext, label in text_file_extensions.items():
        tk.Checkbutton(root, text=f"{label} 파일 복사", variable=copy_text_files[ext]).pack(anchor="w")

    # 이미지 파일 체크박스 추가
    tk.Checkbutton(root, text="이미지 파일 복사 (JPG, PNG)", variable=copy_image_files).pack(anchor="w")

    tk.Button(root, text="모두 선택", command=select_all_checkboxes).pack(pady=10)  # 모두 선택 버튼 추가

    tk.Button(root, text="작업 시작", command=start_process).pack(pady=20)

    root.mainloop()

# 프로그램 실행
if __name__ == "__main__":
    A_folder = None
    B_folder = None
    db_name = None
    db_user = None
    db_password = None
    run_gui()
