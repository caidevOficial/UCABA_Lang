fn main() {
    #[cfg(windows)]
    {
        let mut res = winres::WindowsResource::new();
        res.set_icon("../../ucaba_icon.ico");
        res.set("ProductName", "UCABA");
        res.set("FileDescription", "UCABA: Lenguaje de programación de pseudocódigo en español fuertemente tipado (Rust Engine)");
        res.set("LegalCopyright", "Copyright (c) 2026 Facu Falcone");
        res.set("FileVersion", "2.0.1.0");
        res.set("ProductVersion", "2.0.1.0");
        if let Err(e) = res.compile() {
            eprintln!("Cargo build warning: could not compile Windows resource: {}", e);
        }
    }
}
