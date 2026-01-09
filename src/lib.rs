//! cookcrab_parser: Parse Rust crates and expose API to Python
//!
//! This module uses `syn` to parse Rust source files and extracts
//! public API information (functions, structs, enums, impl blocks)
//! for generating Python type stubs.

use pyo3::prelude::*;
use std::fs;
use std::path::Path;
use syn::{
    visit::Visit, FnArg, ImplItem, ItemConst, ItemEnum, ItemFn, ItemImpl, ItemMacro, ItemStatic,
    ItemStruct, ItemType, ItemUse, Pat, ReturnType, Type, UseTree, Visibility,
};
use walkdir::WalkDir;

/// Structured type information extracted from Rust types
/// This preserves semantic information that would be lost by simple stringification
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustTypeInfo {
    /// The full stringified type (for backwards compatibility)
    #[pyo3(get)]
    pub full_type: String,
    /// Whether this is a reference type (&T or &mut T)
    #[pyo3(get)]
    pub is_reference: bool,
    /// Whether this is a mutable reference (&mut T)
    #[pyo3(get)]
    pub is_mutable_ref: bool,
    /// Whether this is an impl Trait type
    #[pyo3(get)]
    pub is_impl_trait: bool,
    /// The trait bound if is_impl_trait (e.g., "AsRef<[u8]>", "Into<String>")
    #[pyo3(get)]
    pub trait_bound: Option<String>,
    /// The core type name without references/lifetimes
    #[pyo3(get)]
    pub core_type: String,
    /// Whether this type typically borrows input (based on AsRef, Borrow, etc.)
    #[pyo3(get)]
    pub expects_borrow: bool,
    /// Whether this type typically takes ownership (based on Into, T without bounds)
    #[pyo3(get)]
    pub expects_owned: bool,
}

#[pymethods]
impl RustTypeInfo {
    fn __repr__(&self) -> String {
        format!(
            "RustTypeInfo(full='{}', ref={}, impl_trait={}, borrow={}, owned={})",
            self.full_type, self.is_reference, self.is_impl_trait,
            self.expects_borrow, self.expects_owned
        )
    }
}

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
    /// Structured type information for smarter code generation
    #[pyo3(get)]
    pub type_info: Option<RustTypeInfo>,
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
    #[pyo3(get)]
    pub module_path: String,
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
    #[pyo3(get)]
    pub module_path: String,
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
    #[pyo3(get)]
    pub module_path: String,
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

/// A parsed Rust constant (const X: Type = value;)
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustConstant {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub rust_type: String,
    #[pyo3(get)]
    pub is_pub: bool,
    #[pyo3(get)]
    pub doc: Option<String>,
    #[pyo3(get)]
    pub module_path: String, // Track which module this constant is in
}

#[pymethods]
impl RustConstant {
    fn __repr__(&self) -> String {
        format!(
            "RustConstant(name='{}', type='{}', module='{}', is_pub={})",
            self.name, self.rust_type, self.module_path, self.is_pub
        )
    }
}

/// A parsed Rust static (static X: Type = value;)
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustStatic {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub rust_type: String,
    #[pyo3(get)]
    pub is_pub: bool,
    #[pyo3(get)]
    pub is_mut: bool,
    #[pyo3(get)]
    pub doc: Option<String>,
    #[pyo3(get)]
    pub module_path: String,
}

#[pymethods]
impl RustStatic {
    fn __repr__(&self) -> String {
        format!(
            "RustStatic(name='{}', type='{}', module='{}', is_pub={}, is_mut={})",
            self.name, self.rust_type, self.module_path, self.is_pub, self.is_mut
        )
    }
}

/// A re-export of an enum variant with an alias (pub use EnumType::Variant as Alias)
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustEnumVariantAlias {
    #[pyo3(get)]
    pub alias_name: String, // The exported name (e.g., "HS256")
    #[pyo3(get)]
    pub enum_type: String, // The enum type (e.g., "HmacJwsAlgorithm")
    #[pyo3(get)]
    pub variant_name: String, // The variant (e.g., "Hs256")
    #[pyo3(get)]
    pub full_path: String, // Full original path (e.g., "HmacJwsAlgorithm::Hs256")
    #[pyo3(get)]
    pub is_pub: bool,
    #[pyo3(get)]
    pub module_path: String, // The module path where this re-export was made (e.g., "jws")
}

#[pymethods]
impl RustEnumVariantAlias {
    fn __repr__(&self) -> String {
        format!(
            "RustEnumVariantAlias(alias='{}', enum='{}', variant='{}', path='{}')",
            self.alias_name, self.enum_type, self.variant_name, self.full_path
        )
    }
}

/// A parsed Rust macro (macro_rules! or #[macro_export])
/// Macros can't be fully auto-detected by syn, but we can find exported ones
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustMacro {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub doc: Option<String>,
    #[pyo3(get)]
    pub module_path: String,
    /// Whether this macro is exported (#[macro_export])
    #[pyo3(get)]
    pub is_exported: bool,
}

#[pymethods]
impl RustMacro {
    fn __repr__(&self) -> String {
        format!(
            "RustMacro(name='{}', module='{}', exported={})",
            self.name, self.module_path, self.is_exported
        )
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
    #[pyo3(get)]
    pub constants: Vec<RustConstant>,
    #[pyo3(get)]
    pub statics: Vec<RustStatic>,
    #[pyo3(get)]
    pub enum_variant_aliases: Vec<RustEnumVariantAlias>,
    /// Detected macros (macro_rules! with #[macro_export])
    #[pyo3(get)]
    pub macros: Vec<RustMacro>,
    /// All available features defined in Cargo.toml [features] section
    #[pyo3(get)]
    pub available_features: Vec<String>,
    /// Default features (features listed under "default" in [features])
    #[pyo3(get)]
    pub default_features: Vec<String>,
}

#[pymethods]
impl RustCrate {
    fn __repr__(&self) -> String {
        format!(
            "RustCrate(name='{}', functions={}, structs={}, enums={}, impls={}, type_aliases={}, reexports={}, constants={}, statics={}, enum_variant_aliases={}, macros={}, features={})",
            self.name,
            self.functions.len(),
            self.structs.len(),
            self.enums.len(),
            self.impls.len(),
            self.type_aliases.len(),
            self.reexports.len(),
            self.constants.len(),
            self.statics.len(),
            self.enum_variant_aliases.len(),
            self.macros.len(),
            self.available_features.len()
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
    constants: Vec<RustConstant>,
    statics: Vec<RustStatic>,
    enum_variant_aliases: Vec<RustEnumVariantAlias>,
    macros: Vec<RustMacro>,
    current_module: String, // Track current module path
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
            constants: Vec::new(),
            statics: Vec::new(),
            enum_variant_aliases: Vec::new(),
            macros: Vec::new(),
            current_module: String::new(),
        }
    }

    fn with_module(module_path: &str) -> Self {
        Self {
            functions: Vec::new(),
            structs: Vec::new(),
            enums: Vec::new(),
            impls: Vec::new(),
            type_aliases: Vec::new(),
            reexports: Vec::new(),
            constants: Vec::new(),
            statics: Vec::new(),
            enum_variant_aliases: Vec::new(),
            macros: Vec::new(),
            current_module: module_path.to_string(),
        }
    }
}

impl<'ast> Visit<'ast> for ItemCollector {
    fn visit_item_fn(&mut self, node: &'ast ItemFn) {
        if is_pub(&node.vis) {
            self.functions.push(parse_function(node, &self.current_module));
        }
        syn::visit::visit_item_fn(self, node);
    }

    fn visit_item_struct(&mut self, node: &'ast ItemStruct) {
        if is_pub(&node.vis) {
            self.structs.push(parse_struct(node, &self.current_module));
        }
        syn::visit::visit_item_struct(self, node);
    }

    fn visit_item_enum(&mut self, node: &'ast ItemEnum) {
        if is_pub(&node.vis) {
            self.enums.push(parse_enum(node, &self.current_module));
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
        // Only track public re-exports
        if is_pub(&node.vis) {
            // Try to parse as enum variant alias (pub use EnumType::Variant as Alias)
            if let Some(alias) = parse_enum_variant_alias(&node.tree, &self.current_module) {
                self.enum_variant_aliases.push(alias);
            } else if let Some(reexport) = parse_reexport(&node.tree) {
                // Otherwise try as external crate re-export
                self.reexports.push(reexport);
            }
        }
        syn::visit::visit_item_use(self, node);
    }

    fn visit_item_const(&mut self, node: &'ast ItemConst) {
        if is_pub(&node.vis) {
            let name = node.ident.to_string();
            let rust_type = type_to_string(&node.ty);
            let doc = extract_doc_comment(&node.attrs);

            self.constants.push(RustConstant {
                name,
                rust_type,
                is_pub: true,
                doc,
                module_path: self.current_module.clone(),
            });
        }
        syn::visit::visit_item_const(self, node);
    }

    fn visit_item_static(&mut self, node: &'ast ItemStatic) {
        if is_pub(&node.vis) {
            let name = node.ident.to_string();
            let rust_type = type_to_string(&node.ty);
            let doc = extract_doc_comment(&node.attrs);
            let is_mut = matches!(node.mutability, syn::StaticMutability::Mut(_));

            self.statics.push(RustStatic {
                name,
                rust_type,
                is_pub: true,
                is_mut,
                doc,
                module_path: self.current_module.clone(),
            });
        }
        syn::visit::visit_item_static(self, node);
    }

    fn visit_item_macro(&mut self, node: &'ast ItemMacro) {
        // Check if this is a macro_rules! definition with #[macro_export]
        // macro_rules! macros are identified by: mac.path being "macro_rules"
        let is_macro_rules = node.mac.path.is_ident("macro_rules");

        // Check for #[macro_export] attribute
        let is_exported = node.attrs.iter().any(|attr| attr.path().is_ident("macro_export"));

        // Only collect exported macro_rules! definitions
        if is_macro_rules && is_exported {
            // Get macro name from ident if present
            if let Some(ident) = &node.ident {
                let name = ident.to_string();
                let doc = extract_doc_comment(&node.attrs);

                self.macros.push(RustMacro {
                    name,
                    doc,
                    module_path: self.current_module.clone(),
                    is_exported: true,
                });
            }
        }
        syn::visit::visit_item_macro(self, node);
    }
}

/// Parse a use tree to extract enum variant alias (pub use EnumType::Variant as Alias)
fn parse_enum_variant_alias(tree: &UseTree, module_path: &str) -> Option<RustEnumVariantAlias> {
    // We're looking for patterns like: EnumType::Variant as Alias
    // The tree structure for "HmacJwsAlgorithm::Hs256 as HS256" is:
    // Path { ident: "HmacJwsAlgorithm", tree: Path { ident: "Hs256", tree: Rename { .. } } }
    // OR without alias: Path { ident: "EnumType", tree: Name { ident: "Variant" } }
    match tree {
        UseTree::Path(path) => {
            let first_segment = path.ident.to_string();

            // Check if this looks like a type name (starts with uppercase)
            // This heuristic helps distinguish "EnumType::Variant" from "crate::module"
            if !first_segment.chars().next().map(|c| c.is_uppercase()).unwrap_or(false) {
                return None;
            }

            match &*path.tree {
                // EnumType::Variant as Alias
                UseTree::Rename(rename) => {
                    let variant_name = rename.ident.to_string();
                    let alias_name = rename.rename.to_string();
                    Some(RustEnumVariantAlias {
                        alias_name,
                        enum_type: first_segment.clone(),
                        variant_name: variant_name.clone(),
                        full_path: format!("{}::{}", first_segment, variant_name),
                        is_pub: true,
                        module_path: module_path.to_string(),
                    })
                }
                // EnumType::Variant (no alias, same name)
                UseTree::Name(name) => {
                    let variant_name = name.ident.to_string();
                    Some(RustEnumVariantAlias {
                        alias_name: variant_name.clone(),
                        enum_type: first_segment.clone(),
                        variant_name: variant_name.clone(),
                        full_path: format!("{}::{}", first_segment, variant_name),
                        is_pub: true,
                        module_path: module_path.to_string(),
                    })
                }
                // Nested path like OuterType::InnerType::Variant as Alias
                UseTree::Path(inner_path) => {
                    let second_segment = inner_path.ident.to_string();
                    match &*inner_path.tree {
                        UseTree::Rename(rename) => {
                            let variant_name = rename.ident.to_string();
                            let alias_name = rename.rename.to_string();
                            Some(RustEnumVariantAlias {
                                alias_name,
                                enum_type: format!("{}::{}", first_segment, second_segment),
                                variant_name: variant_name.clone(),
                                full_path: format!("{}::{}::{}", first_segment, second_segment, variant_name),
                                is_pub: true,
                                module_path: module_path.to_string(),
                            })
                        }
                        UseTree::Name(name) => {
                            let variant_name = name.ident.to_string();
                            Some(RustEnumVariantAlias {
                                alias_name: variant_name.clone(),
                                enum_type: format!("{}::{}", first_segment, second_segment),
                                variant_name: variant_name.clone(),
                                full_path: format!("{}::{}::{}", first_segment, second_segment, variant_name),
                                is_pub: true,
                                module_path: module_path.to_string(),
                            })
                        }
                        _ => None,
                    }
                }
                _ => None,
            }
        }
        _ => None,
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

/// Analyze a type and extract structured information
fn analyze_type(ty: &Type) -> RustTypeInfo {
    use quote::ToTokens;

    let full_type = ty.to_token_stream().to_string().replace(' ', "");
    let mut is_reference = false;
    let mut is_mutable_ref = false;
    let mut is_impl_trait = false;
    let mut trait_bound: Option<String> = None;
    let mut core_type = full_type.clone();
    let mut expects_borrow = false;
    let mut expects_owned = false;

    match ty {
        Type::Reference(type_ref) => {
            is_reference = true;
            is_mutable_ref = type_ref.mutability.is_some();
            // Extract the inner type as core_type
            core_type = type_to_string(&type_ref.elem);
            expects_borrow = true;
        }
        Type::ImplTrait(impl_trait) => {
            is_impl_trait = true;
            // Extract the trait bounds
            let bounds: Vec<String> = impl_trait.bounds.iter()
                .map(|b| b.to_token_stream().to_string().replace(' ', ""))
                .collect();
            let bound_str = bounds.join("+");
            trait_bound = Some(bound_str.clone());

            // Determine borrow vs ownership based on common trait patterns
            // AsRef, Borrow, AsMut -> expects borrow (but accepts owned too)
            // Into, TryInto -> expects ownership
            let bound_lower = bound_str.to_lowercase();
            if bound_lower.contains("asref") || bound_lower.contains("borrow")
                || bound_lower.contains("asmut") {
                expects_borrow = true;
            }
            if bound_lower.contains("into") || bound_lower.contains("tryinto") {
                expects_owned = true;
            }

            // Core type is the trait bound itself for impl Trait
            core_type = bound_str;
        }
        Type::Path(type_path) => {
            // Extract the last segment as core type
            if let Some(last_seg) = type_path.path.segments.last() {
                core_type = last_seg.ident.to_string();

                // Check for generic parameters like Option<T>, Vec<T>
                if !last_seg.arguments.is_empty() {
                    core_type = format!(
                        "{}{}",
                        last_seg.ident,
                        last_seg.arguments.to_token_stream().to_string().replace(' ', "")
                    );
                }
            }
        }
        _ => {}
    }

    RustTypeInfo {
        full_type,
        is_reference,
        is_mutable_ref,
        is_impl_trait,
        trait_bound,
        core_type,
        expects_borrow,
        expects_owned,
    }
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

fn parse_function(node: &ItemFn, module_path: &str) -> RustFunction {
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
        module_path: module_path.to_string(),
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

fn parse_fn_params(
    inputs: &syn::punctuated::Punctuated<FnArg, syn::token::Comma>,
) -> Vec<RustParam> {
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
                let type_info = Some(analyze_type(&pat_type.ty));
                Some(RustParam {
                    name,
                    rust_type,
                    is_self: false,
                    is_mut: false,
                    type_info,
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
                let type_info = Some(analyze_type(&pat_type.ty));
                Some(RustParam {
                    name,
                    rust_type,
                    is_self: false,
                    is_mut: false,
                    type_info,
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

fn parse_struct(node: &ItemStruct, module_path: &str) -> RustStruct {
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
        module_path: module_path.to_string(),
    }
}

fn parse_enum(node: &ItemEnum, module_path: &str) -> RustEnum {
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
        module_path: module_path.to_string(),
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

/// Parse a single Rust source file with optional module path
fn parse_file_internal(path: &str, module_path: &str) -> PyResult<RustCrate> {
    let content = fs::read_to_string(path).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to read file: {}", e))
    })?;

    let syntax = syn::parse_file(&content).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Failed to parse Rust: {}", e))
    })?;

    let mut collector = ItemCollector::new();
    collector.current_module = module_path.to_string();
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
        constants: collector.constants,
        statics: collector.statics,
        enum_variant_aliases: collector.enum_variant_aliases,
        macros: collector.macros,
        available_features: Vec::new(),  // Single file has no Cargo.toml
        default_features: Vec::new(),
    })
}

/// Parse a single Rust source file (public API)
#[pyfunction]
fn parse_file(path: &str) -> PyResult<RustCrate> {
    parse_file_internal(path, "")
}

/// Parse features from Cargo.toml content
/// Returns (available_features, default_features)
fn parse_cargo_features(content: &str) -> (Vec<String>, Vec<String>) {
    let mut available_features = Vec::new();
    let mut default_features = Vec::new();

    // Parse the TOML content
    if let Ok(parsed) = content.parse::<toml::Table>() {
        if let Some(toml::Value::Table(features)) = parsed.get("features") {
            for (name, value) in features {
                // Add all feature names to available_features
                available_features.push(name.clone());

                // If this is the "default" feature, extract its dependencies as default_features
                if name == "default" {
                    if let toml::Value::Array(deps) = value {
                        for dep in deps {
                            if let toml::Value::String(dep_name) = dep {
                                default_features.push(dep_name.clone());
                            }
                        }
                    }
                }
            }
        }
    }

    // Sort for consistent output
    available_features.sort();
    default_features.sort();

    (available_features, default_features)
}

/// Parse an entire Rust crate directory
#[pyfunction]
fn parse_crate(path: &str) -> PyResult<RustCrate> {
    let crate_path = Path::new(path);

    // Try to find crate name and features from Cargo.toml
    let cargo_toml = crate_path.join("Cargo.toml");
    let (crate_name, available_features, default_features) = if cargo_toml.exists() {
        let content = fs::read_to_string(&cargo_toml).unwrap_or_default();

        // Extract crate name - look for name = "..."
        let name = content
            .lines()
            .find(|l| l.trim().starts_with("name"))
            .and_then(|l| l.split('=').nth(1))
            .map(|s| s.trim().trim_matches('"').to_string())
            .unwrap_or_else(|| "unknown".to_string());

        // Extract features
        let (avail, defaults) = parse_cargo_features(&content);

        (name, avail, defaults)
    } else {
        (
            crate_path
                .file_name()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_else(|| "unknown".to_string()),
            Vec::new(),
            Vec::new(),
        )
    };

    let src_path = crate_path.join("src");
    let search_path = if src_path.exists() {
        &src_path
    } else {
        crate_path
    };

    let mut all_functions = Vec::new();
    let mut all_structs = Vec::new();
    let mut all_enums = Vec::new();
    let mut all_impls = Vec::new();
    let mut all_type_aliases = Vec::new();
    let mut all_reexports = Vec::new();
    let mut all_constants = Vec::new();
    let mut all_statics = Vec::new();
    let mut all_enum_variant_aliases = Vec::new();
    let mut all_macros = Vec::new();

    for entry in WalkDir::new(search_path)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().map(|ext| ext == "rs").unwrap_or(false))
    {
        let file_path = entry.path();

        // Compute module path from file path relative to search_path
        // e.g., src/jws/mod.rs -> "jws", src/jws/alg/hmac.rs -> "jws::alg::hmac"
        let module_path = file_path
            .strip_prefix(search_path)
            .ok()
            .and_then(|rel| {
                let mut parts: Vec<&str> = rel
                    .components()
                    .filter_map(|c| c.as_os_str().to_str())
                    .collect();
                // Remove the file name
                if let Some(last) = parts.last() {
                    if last.ends_with(".rs") {
                        parts.pop();
                    }
                }
                // If the file was mod.rs or lib.rs, use the parent path
                if let Some(stem) = file_path.file_stem().and_then(|s| s.to_str()) {
                    if stem != "mod" && stem != "lib" {
                        // For regular files like alg/hmac.rs, add the stem
                        parts.push(stem);
                    }
                }
                if parts.is_empty() {
                    Some(String::new())
                } else {
                    Some(parts.join("::"))
                }
            })
            .unwrap_or_default();

        match parse_file_internal(file_path.to_str().unwrap_or_default(), &module_path) {
            Ok(parsed) => {
                all_functions.extend(parsed.functions);
                all_structs.extend(parsed.structs);
                all_enums.extend(parsed.enums);
                all_impls.extend(parsed.impls);
                all_type_aliases.extend(parsed.type_aliases);
                all_reexports.extend(parsed.reexports);
                all_constants.extend(parsed.constants);
                all_statics.extend(parsed.statics);
                all_enum_variant_aliases.extend(parsed.enum_variant_aliases);
                all_macros.extend(parsed.macros);
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
        constants: all_constants,
        statics: all_statics,
        enum_variant_aliases: all_enum_variant_aliases,
        macros: all_macros,
        available_features,
        default_features,
    })
}

// =============================================================================
// Rust Code Validation and Formatting Functions (for transpilation)
// =============================================================================

/// Validate Rust source code syntax using syn
///
/// Returns True if the code is valid Rust syntax, raises SyntaxError otherwise.
#[pyfunction]
fn validate_rust_code(code: &str) -> PyResult<bool> {
    match syn::parse_file(code) {
        Ok(_) => Ok(true),
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PySyntaxError, _>(format!(
            "Invalid Rust syntax: {}",
            e
        ))),
    }
}

/// Format Rust source code using prettyplease
///
/// Returns formatted code if valid, raises SyntaxError if code cannot be parsed.
#[pyfunction]
fn format_rust_code(code: &str) -> PyResult<String> {
    let syntax_tree = syn::parse_file(code).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PySyntaxError, _>(format!(
            "Cannot format invalid Rust: {}",
            e
        ))
    })?;
    Ok(prettyplease::unparse(&syntax_tree))
}

/// Validate and format Rust source code in one call (most efficient)
///
/// Returns formatted code if valid, raises SyntaxError with location info if invalid.
#[pyfunction]
fn validate_and_format_rust(code: &str) -> PyResult<String> {
    let syntax_tree = syn::parse_file(code).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PySyntaxError, _>(format!(
            "Invalid Rust syntax: {}",
            e
        ))
    })?;
    Ok(prettyplease::unparse(&syntax_tree))
}

/// cookcrab._parser Python module
#[pymodule]
fn _parser(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_file, m)?)?;
    m.add_function(wrap_pyfunction!(parse_crate, m)?)?;
    // Rust validation/formatting functions
    m.add_function(wrap_pyfunction!(validate_rust_code, m)?)?;
    m.add_function(wrap_pyfunction!(format_rust_code, m)?)?;
    m.add_function(wrap_pyfunction!(validate_and_format_rust, m)?)?;
    m.add_class::<RustTypeInfo>()?;
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
    m.add_class::<RustConstant>()?;
    m.add_class::<RustStatic>()?;
    m.add_class::<RustEnumVariantAlias>()?;
    m.add_class::<RustMacro>()?;
    Ok(())
}
