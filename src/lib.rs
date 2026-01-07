//! cookcrab_parser: Parse Rust crates and expose API to Python
//!
//! This module uses `syn` to parse Rust source files and extracts
//! public API information (functions, structs, enums, impl blocks)
//! for generating Python type stubs.

use pyo3::prelude::*;
use std::fs;
use std::path::Path;
use syn::{
    visit::Visit, FnArg, ImplItem, ItemEnum, ItemFn, ItemImpl, ItemStruct, ItemType, ItemUse,
    Pat, ReturnType, Type, UseTree, Visibility,
};
use walkdir::WalkDir;

/// A parsed Rust function parameter
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustParam {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub rust_type: String,
    #[pyo3(get)]
    pub is_self: bool,
    #[pyo3(get)]
    pub is_mut: bool,
}

#[pymethods]
impl RustParam {
    fn __repr__(&self) -> String {
        format!(
            "RustParam(name='{}', rust_type='{}', is_self={}, is_mut={})",
            self.name, self.rust_type, self.is_self, self.is_mut
        )
    }
}

/// A parsed Rust function
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustFunction {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub params: Vec<RustParam>,
    #[pyo3(get)]
    pub return_type: Option<String>,
    #[pyo3(get)]
    pub is_pub: bool,
    #[pyo3(get)]
    pub is_async: bool,
    #[pyo3(get)]
    pub doc: Option<String>,
}

#[pymethods]
impl RustFunction {
    fn __repr__(&self) -> String {
        format!(
            "RustFunction(name='{}', params={}, return_type={:?}, is_pub={})",
            self.name,
            self.params.len(),
            self.return_type,
            self.is_pub
        )
    }
}

/// A parsed Rust struct field
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustField {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub rust_type: String,
    #[pyo3(get)]
    pub is_pub: bool,
}

#[pymethods]
impl RustField {
    fn __repr__(&self) -> String {
        format!(
            "RustField(name='{}', rust_type='{}', is_pub={})",
            self.name, self.rust_type, self.is_pub
        )
    }
}

/// A parsed Rust struct
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustStruct {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub fields: Vec<RustField>,
    #[pyo3(get)]
    pub is_pub: bool,
    #[pyo3(get)]
    pub doc: Option<String>,
}

#[pymethods]
impl RustStruct {
    fn __repr__(&self) -> String {
        format!(
            "RustStruct(name='{}', fields={}, is_pub={})",
            self.name,
            self.fields.len(),
            self.is_pub
        )
    }
}

/// A parsed Rust enum variant
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustVariant {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub fields: Vec<RustField>,
}

#[pymethods]
impl RustVariant {
    fn __repr__(&self) -> String {
        format!(
            "RustVariant(name='{}', fields={})",
            self.name,
            self.fields.len()
        )
    }
}

/// A parsed Rust enum
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustEnum {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub variants: Vec<RustVariant>,
    #[pyo3(get)]
    pub is_pub: bool,
    #[pyo3(get)]
    pub doc: Option<String>,
}

#[pymethods]
impl RustEnum {
    fn __repr__(&self) -> String {
        format!(
            "RustEnum(name='{}', variants={}, is_pub={})",
            self.name,
            self.variants.len(),
            self.is_pub
        )
    }
}

/// A parsed Rust method (from impl block)
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustMethod {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub params: Vec<RustParam>,
    #[pyo3(get)]
    pub return_type: Option<String>,
    #[pyo3(get)]
    pub self_type: String, // "", "&self", "&mut self", "self"
    #[pyo3(get)]
    pub is_pub: bool,
    #[pyo3(get)]
    pub is_static: bool, // No self parameter
    #[pyo3(get)]
    pub doc: Option<String>,
}

#[pymethods]
impl RustMethod {
    fn __repr__(&self) -> String {
        format!(
            "RustMethod(name='{}', self_type='{}', params={}, return_type={:?})",
            self.name,
            self.self_type,
            self.params.len(),
            self.return_type
        )
    }
}

/// A parsed Rust impl block
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustImpl {
    #[pyo3(get)]
    pub type_name: String,
    #[pyo3(get)]
    pub methods: Vec<RustMethod>,
    #[pyo3(get)]
    pub trait_name: Option<String>,
}

#[pymethods]
impl RustImpl {
    fn __repr__(&self) -> String {
        format!(
            "RustImpl(type_name='{}', methods={}, trait={:?})",
            self.type_name,
            self.methods.len(),
            self.trait_name
        )
    }
}

/// A parsed Rust type alias (e.g., pub type Result<T> = core::result::Result<T, Error>;)
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustTypeAlias {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub target_type: String,
    #[pyo3(get)]
    pub generics: Vec<String>,
    #[pyo3(get)]
    pub is_pub: bool,
    #[pyo3(get)]
    pub doc: Option<String>,
}

#[pymethods]
impl RustTypeAlias {
    fn __repr__(&self) -> String {
        format!(
            "RustTypeAlias(name='{}', target='{}', generics={:?})",
            self.name, self.target_type, self.generics
        )
    }
}

/// A parsed Rust re-export (pub use other_crate::*)
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustReexport {
    #[pyo3(get)]
    pub source_crate: String,
    #[pyo3(get)]
    pub is_glob: bool, // true for `pub use crate::*`
    #[pyo3(get)]
    pub items: Vec<String>, // specific items if not glob
}

#[pymethods]
impl RustReexport {
    fn __repr__(&self) -> String {
        if self.is_glob {
            format!("RustReexport(source='{}', glob=true)", self.source_crate)
        } else {
            format!(
                "RustReexport(source='{}', items={:?})",
                self.source_crate, self.items
            )
        }
    }
}

/// A parsed Rust crate
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustCrate {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub functions: Vec<RustFunction>,
    #[pyo3(get)]
    pub structs: Vec<RustStruct>,
    #[pyo3(get)]
    pub enums: Vec<RustEnum>,
    #[pyo3(get)]
    pub impls: Vec<RustImpl>,
    #[pyo3(get)]
    pub type_aliases: Vec<RustTypeAlias>,
    #[pyo3(get)]
    pub reexports: Vec<RustReexport>,
}

#[pymethods]
impl RustCrate {
    fn __repr__(&self) -> String {
        format!(
            "RustCrate(name='{}', functions={}, structs={}, enums={}, impls={}, type_aliases={}, reexports={})",
            self.name,
            self.functions.len(),
            self.structs.len(),
            self.enums.len(),
            self.impls.len(),
            self.type_aliases.len(),
            self.reexports.len()
        )
    }
}

/// Visitor to collect items from a Rust source file
struct ItemCollector {
    functions: Vec<RustFunction>,
    structs: Vec<RustStruct>,
    enums: Vec<RustEnum>,
    impls: Vec<RustImpl>,
    type_aliases: Vec<RustTypeAlias>,
    reexports: Vec<RustReexport>,
}

impl ItemCollector {
    fn new() -> Self {
        Self {
            functions: Vec::new(),
            structs: Vec::new(),
            enums: Vec::new(),
            impls: Vec::new(),
            type_aliases: Vec::new(),
            reexports: Vec::new(),
        }
    }
}

impl<'ast> Visit<'ast> for ItemCollector {
    fn visit_item_fn(&mut self, node: &'ast ItemFn) {
        if is_pub(&node.vis) {
            self.functions.push(parse_function(node));
        }
        syn::visit::visit_item_fn(self, node);
    }

    fn visit_item_struct(&mut self, node: &'ast ItemStruct) {
        if is_pub(&node.vis) {
            self.structs.push(parse_struct(node));
        }
        syn::visit::visit_item_struct(self, node);
    }

    fn visit_item_enum(&mut self, node: &'ast ItemEnum) {
        if is_pub(&node.vis) {
            self.enums.push(parse_enum(node));
        }
        syn::visit::visit_item_enum(self, node);
    }

    fn visit_item_impl(&mut self, node: &'ast ItemImpl) {
        // Only collect impl blocks for types (not trait impls for external types)
        if let Type::Path(type_path) = &*node.self_ty {
            let type_name = type_path
                .path
                .segments
                .last()
                .map(|s| s.ident.to_string())
                .unwrap_or_default();

            let trait_name = node.trait_.as_ref().map(|(_, path, _)| {
                path.segments
                    .last()
                    .map(|s| s.ident.to_string())
                    .unwrap_or_default()
            });

            let methods: Vec<RustMethod> = node
                .items
                .iter()
                .filter_map(|item| {
                    if let ImplItem::Fn(method) = item {
                        if is_pub(&method.vis) || node.trait_.is_some() {
                            Some(parse_method(method))
                        } else {
                            None
                        }
                    } else {
                        None
                    }
                })
                .collect();

            if !methods.is_empty() {
                self.impls.push(RustImpl {
                    type_name,
                    methods,
                    trait_name,
                });
            }
        }
        syn::visit::visit_item_impl(self, node);
    }

    fn visit_item_type(&mut self, node: &'ast ItemType) {
        if is_pub(&node.vis) {
            self.type_aliases.push(parse_type_alias(node));
        }
        syn::visit::visit_item_type(self, node);
    }

    fn visit_item_use(&mut self, node: &'ast ItemUse) {
        // Only track public re-exports from external crates
        if is_pub(&node.vis) {
            if let Some(reexport) = parse_reexport(&node.tree) {
                self.reexports.push(reexport);
            }
        }
        syn::visit::visit_item_use(self, node);
    }
}

/// Parse a use tree to extract re-export information
fn parse_reexport(tree: &UseTree) -> Option<RustReexport> {
    match tree {
        UseTree::Path(path) => {
            let first_segment = path.ident.to_string();
            // Skip crate-internal paths (self, super, crate)
            if first_segment == "self" || first_segment == "super" || first_segment == "crate" {
                return None;
            }
            // Recursively check the rest of the path
            match &*path.tree {
                UseTree::Glob(_) => Some(RustReexport {
                    source_crate: first_segment,
                    is_glob: true,
                    items: Vec::new(),
                }),
                UseTree::Group(group) => {
                    let items: Vec<String> = group
                        .items
                        .iter()
                        .filter_map(|item| match item {
                            UseTree::Name(name) => Some(name.ident.to_string()),
                            UseTree::Rename(rename) => Some(rename.ident.to_string()),
                            _ => None,
                        })
                        .collect();
                    if !items.is_empty() {
                        Some(RustReexport {
                            source_crate: first_segment,
                            is_glob: false,
                            items,
                        })
                    } else {
                        None
                    }
                }
                UseTree::Path(inner) => {
                    // Handle nested paths like clap_builder::builder::Command
                    parse_reexport(&UseTree::Path(inner.clone())).map(|mut r| {
                        r.source_crate = first_segment;
                        r
                    })
                }
                _ => None,
            }
        }
        UseTree::Glob(_) => None, // Top-level glob without path
        _ => None,
    }
}

fn is_pub(vis: &Visibility) -> bool {
    matches!(vis, Visibility::Public(_))
}

fn type_to_string(ty: &Type) -> String {
    use quote::ToTokens;
    ty.to_token_stream().to_string().replace(' ', "")
}

fn extract_doc_comment(attrs: &[syn::Attribute]) -> Option<String> {
    let docs: Vec<String> = attrs
        .iter()
        .filter_map(|attr| {
            if attr.path().is_ident("doc") {
                if let syn::Meta::NameValue(nv) = &attr.meta {
                    if let syn::Expr::Lit(syn::ExprLit {
                        lit: syn::Lit::Str(s),
                        ..
                    }) = &nv.value
                    {
                        return Some(s.value().trim().to_string());
                    }
                }
            }
            None
        })
        .collect();

    if docs.is_empty() {
        None
    } else {
        Some(docs.join("\n"))
    }
}

fn parse_function(node: &ItemFn) -> RustFunction {
    let name = node.sig.ident.to_string();
    let params = parse_fn_params(&node.sig.inputs);
    let return_type = parse_return_type(&node.sig.output);
    let is_async = node.sig.asyncness.is_some();
    let doc = extract_doc_comment(&node.attrs);

    RustFunction {
        name,
        params,
        return_type,
        is_pub: true,
        is_async,
        doc,
    }
}

fn parse_method(node: &syn::ImplItemFn) -> RustMethod {
    let name = node.sig.ident.to_string();
    let (params, self_type) = parse_method_params(&node.sig.inputs);
    let return_type = parse_return_type(&node.sig.output);
    let is_static = self_type.is_empty();
    let doc = extract_doc_comment(&node.attrs);

    RustMethod {
        name,
        params,
        return_type,
        self_type,
        is_pub: true,
        is_static,
        doc,
    }
}

fn parse_fn_params(inputs: &syn::punctuated::Punctuated<FnArg, syn::token::Comma>) -> Vec<RustParam> {
    inputs
        .iter()
        .filter_map(|arg| {
            if let FnArg::Typed(pat_type) = arg {
                let name = if let Pat::Ident(pat_ident) = &*pat_type.pat {
                    pat_ident.ident.to_string()
                } else {
                    "_".to_string()
                };
                let rust_type = type_to_string(&pat_type.ty);
                Some(RustParam {
                    name,
                    rust_type,
                    is_self: false,
                    is_mut: false,
                })
            } else {
                None
            }
        })
        .collect()
}

fn parse_method_params(
    inputs: &syn::punctuated::Punctuated<FnArg, syn::token::Comma>,
) -> (Vec<RustParam>, String) {
    let mut self_type = String::new();
    let params: Vec<RustParam> = inputs
        .iter()
        .filter_map(|arg| match arg {
            FnArg::Receiver(recv) => {
                self_type = if recv.reference.is_some() {
                    if recv.mutability.is_some() {
                        "&mut self".to_string()
                    } else {
                        "&self".to_string()
                    }
                } else {
                    "self".to_string()
                };
                None
            }
            FnArg::Typed(pat_type) => {
                let name = if let Pat::Ident(pat_ident) = &*pat_type.pat {
                    pat_ident.ident.to_string()
                } else {
                    "_".to_string()
                };
                let rust_type = type_to_string(&pat_type.ty);
                Some(RustParam {
                    name,
                    rust_type,
                    is_self: false,
                    is_mut: false,
                })
            }
        })
        .collect();

    (params, self_type)
}

fn parse_return_type(output: &ReturnType) -> Option<String> {
    match output {
        ReturnType::Default => None,
        ReturnType::Type(_, ty) => Some(type_to_string(ty)),
    }
}

fn parse_struct(node: &ItemStruct) -> RustStruct {
    let name = node.ident.to_string();
    let fields = match &node.fields {
        syn::Fields::Named(named) => named
            .named
            .iter()
            .map(|f| RustField {
                name: f.ident.as_ref().map(|i| i.to_string()).unwrap_or_default(),
                rust_type: type_to_string(&f.ty),
                is_pub: is_pub(&f.vis),
            })
            .collect(),
        syn::Fields::Unnamed(unnamed) => unnamed
            .unnamed
            .iter()
            .enumerate()
            .map(|(i, f)| RustField {
                name: format!("_{}", i),
                rust_type: type_to_string(&f.ty),
                is_pub: is_pub(&f.vis),
            })
            .collect(),
        syn::Fields::Unit => Vec::new(),
    };
    let doc = extract_doc_comment(&node.attrs);

    RustStruct {
        name,
        fields,
        is_pub: true,
        doc,
    }
}

fn parse_enum(node: &ItemEnum) -> RustEnum {
    let name = node.ident.to_string();
    let variants = node
        .variants
        .iter()
        .map(|v| {
            let fields = match &v.fields {
                syn::Fields::Named(named) => named
                    .named
                    .iter()
                    .map(|f| RustField {
                        name: f.ident.as_ref().map(|i| i.to_string()).unwrap_or_default(),
                        rust_type: type_to_string(&f.ty),
                        is_pub: true,
                    })
                    .collect(),
                syn::Fields::Unnamed(unnamed) => unnamed
                    .unnamed
                    .iter()
                    .enumerate()
                    .map(|(i, f)| RustField {
                        name: format!("_{}", i),
                        rust_type: type_to_string(&f.ty),
                        is_pub: true,
                    })
                    .collect(),
                syn::Fields::Unit => Vec::new(),
            };
            RustVariant {
                name: v.ident.to_string(),
                fields,
            }
        })
        .collect();
    let doc = extract_doc_comment(&node.attrs);

    RustEnum {
        name,
        variants,
        is_pub: true,
        doc,
    }
}

fn parse_type_alias(node: &ItemType) -> RustTypeAlias {
    let name = node.ident.to_string();
    let target_type = type_to_string(&node.ty);
    let doc = extract_doc_comment(&node.attrs);

    // Extract generic parameters
    let generics: Vec<String> = node
        .generics
        .params
        .iter()
        .map(|param| {
            use quote::ToTokens;
            param.to_token_stream().to_string()
        })
        .collect();

    RustTypeAlias {
        name,
        target_type,
        generics,
        is_pub: true,
        doc,
    }
}

/// Parse a single Rust source file
#[pyfunction]
fn parse_file(path: &str) -> PyResult<RustCrate> {
    let content = fs::read_to_string(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to read file: {}", e)))?;

    let syntax = syn::parse_file(&content)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Failed to parse Rust: {}", e)))?;

    let mut collector = ItemCollector::new();
    collector.visit_file(&syntax);

    let name = Path::new(path)
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_else(|| "unknown".to_string());

    Ok(RustCrate {
        name,
        functions: collector.functions,
        structs: collector.structs,
        enums: collector.enums,
        impls: collector.impls,
        type_aliases: collector.type_aliases,
        reexports: collector.reexports,
    })
}

/// Parse an entire Rust crate directory
#[pyfunction]
fn parse_crate(path: &str) -> PyResult<RustCrate> {
    let crate_path = Path::new(path);

    // Try to find crate name from Cargo.toml
    let cargo_toml = crate_path.join("Cargo.toml");
    let crate_name = if cargo_toml.exists() {
        let content = fs::read_to_string(&cargo_toml).unwrap_or_default();
        // Simple extraction - look for name = "..."
        content
            .lines()
            .find(|l| l.trim().starts_with("name"))
            .and_then(|l| l.split('=').nth(1))
            .map(|s| s.trim().trim_matches('"').to_string())
            .unwrap_or_else(|| "unknown".to_string())
    } else {
        crate_path
            .file_name()
            .map(|s| s.to_string_lossy().to_string())
            .unwrap_or_else(|| "unknown".to_string())
    };

    let src_path = crate_path.join("src");
    let search_path = if src_path.exists() { &src_path } else { crate_path };

    let mut all_functions = Vec::new();
    let mut all_structs = Vec::new();
    let mut all_enums = Vec::new();
    let mut all_impls = Vec::new();
    let mut all_type_aliases = Vec::new();
    let mut all_reexports = Vec::new();

    for entry in WalkDir::new(search_path)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().map(|ext| ext == "rs").unwrap_or(false))
    {
        let file_path = entry.path();
        match parse_file(file_path.to_str().unwrap_or_default()) {
            Ok(parsed) => {
                all_functions.extend(parsed.functions);
                all_structs.extend(parsed.structs);
                all_enums.extend(parsed.enums);
                all_impls.extend(parsed.impls);
                all_type_aliases.extend(parsed.type_aliases);
                all_reexports.extend(parsed.reexports);
            }
            Err(_) => {
                // Skip files that fail to parse
                continue;
            }
        }
    }

    Ok(RustCrate {
        name: crate_name,
        functions: all_functions,
        structs: all_structs,
        enums: all_enums,
        impls: all_impls,
        type_aliases: all_type_aliases,
        reexports: all_reexports,
    })
}

/// cookcrab._parser Python module
#[pymodule]
fn _parser(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_file, m)?)?;
    m.add_function(wrap_pyfunction!(parse_crate, m)?)?;
    m.add_class::<RustParam>()?;
    m.add_class::<RustFunction>()?;
    m.add_class::<RustField>()?;
    m.add_class::<RustTypeAlias>()?;
    m.add_class::<RustStruct>()?;
    m.add_class::<RustVariant>()?;
    m.add_class::<RustEnum>()?;
    m.add_class::<RustMethod>()?;
    m.add_class::<RustImpl>()?;
    m.add_class::<RustCrate>()?;
    m.add_class::<RustReexport>()?;
    Ok(())
}
