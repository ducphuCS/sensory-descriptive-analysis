# ============================================================
# RATA REPLICATED — Discriminating Power & Descriptor Selection
# Data: Book2.xlsx
# Columns: Panelist, Productcode, Product, Rep, [descriptors...]
# ============================================================

library(tidyverse)
library(readxl)
library(lme4)
library(lmerTest)
library(reshape2)
library(ggplot2)
library(ggrepel)

# ------------------------------------------------------------
# 0. LOAD DATA
# ------------------------------------------------------------
df <- read_excel("Book3.xlsx")
names(df) <- trimws(names(df))
df <- df %>% rename(Product = Product, Repetition = Rep)

# Định nghĩa desc_cols trước
desc_cols <- names(df)[4:ncol(df)]

# Rồi mới convert
df <- df %>%
  mutate(across(all_of(desc_cols), ~ as.numeric(.)))

# Descriptor columns = tất cả từ cột 5 trở đi
desc_cols <- names(df)[4:ncol(df)]

cat("=== Cấu trúc data ===\n")
cat("Panelists:", n_distinct(df$Panelist),
    "| Sản phẩm:", n_distinct(df$Product),
    "| Lặp:", n_distinct(df$Repetition),
    "| Descriptors:", length(desc_cols), "\n\n")
cat("Descriptors:\n")
print(desc_cols)
cat("\n")

# ------------------------------------------------------------
# 1. USAGE RATE
# Tỉ lệ observations có score > 0
# ------------------------------------------------------------
usage_rate <- df %>%
  summarise(across(all_of(desc_cols), ~ mean(. > 0, na.rm = TRUE))) %>%
  pivot_longer(everything(), names_to = "Descriptor", values_to = "UsageRate") %>%
  arrange(desc(UsageRate))

cat("=== Usage Rate ===\n")
print(usage_rate, n = Inf)
cat("\n")

# ------------------------------------------------------------
# 2. DISCRIMINATING POWER — Linear Mixed Model
# Score ~ Product + (1|Panelist) + (1|Panelist:Product)
# ------------------------------------------------------------
cat("=== Fitting LMM cho từng descriptor... ===\n")

results_lmm <- map_dfr(desc_cols, function(d) {
  
  dat <- df %>% rename(Score = all_of(d)) %>%
    mutate(
      Product  = factor(Product),
      Panelist = factor(Panelist)
    )
  
  # Thử model đầy đủ, fallback sang model đơn giản nếu lỗi
  mod <- tryCatch({
    suppressMessages(suppressWarnings(
      lmer(Score ~ Product + (1 | Panelist) + (1 | Panelist:Product),
           data = dat, REML = FALSE)
    ))
  }, error = function(e) {
    suppressMessages(suppressWarnings(
      lmer(Score ~ Product + (1 | Panelist),
           data = dat, REML = FALSE)
    ))
  })
  
  an    <- anova(mod, type = "III")
  F_val <- an["Product", "F value"]
  p_val <- an["Product", "Pr(>F)"]
  
  SS_prod  <- an["Product", "Sum Sq"]
  SS_res   <- sum(resid(mod)^2)
  eta2     <- SS_prod / (SS_prod + SS_res)
  
  # Ghi chú descriptor nào phải dùng fallback model
  model_used <- if (length(lme4::findbars(formula(mod))) == 1) "simple" else "full"
  
  tibble(
    Descriptor = d,
    F_product  = round(F_val, 2),
    p_product  = round(p_val, 4),
    eta2       = round(eta2, 4),
    model      = model_used,
    sig        = case_when(
      p_val < 0.001 ~ "***",
      p_val < 0.01  ~ "**",
      p_val < 0.05  ~ "*",
      TRUE          ~ "ns"
    )
  )
})


cat("\n=== Discriminating Power (LMM) ===\n")
print(results_lmm %>% arrange(desc(F_product)), n = Inf)
cat("\n")

# ------------------------------------------------------------
# 3. REPEATABILITY — r giữa Rep 1 và Rep 2
# ------------------------------------------------------------
rep_wide <- df %>%
  pivot_wider(
    id_cols     = c(Panelist, Product),
    names_from  = Repetition,
    values_from = all_of(desc_cols),
    names_sep   = "_Rep"
  )

repeatability <- map_dfr(desc_cols, function(d) {
  r1_col <- paste0(d, "_Rep1")
  r2_col <- paste0(d, "_Rep2")
  if (!r1_col %in% names(rep_wide) | !r2_col %in% names(rep_wide)) {
    return(tibble(Descriptor = d, Repeatability_r = NA_real_))
  }
  r1 <- rep_wide[[r1_col]]
  r2 <- rep_wide[[r2_col]]
  cor_val <- cor(r1, r2, use = "complete.obs", method = "pearson")
  tibble(Descriptor = d, Repeatability_r = round(cor_val, 3))
})

cat("=== Repeatability (r Rep1 vs Rep2) ===\n")
print(repeatability %>% arrange(desc(Repeatability_r)), n = Inf)
cat("\n")

# ------------------------------------------------------------
# 4. BẢNG TỔNG HỢP & QUYẾT ĐỊNH
# ------------------------------------------------------------
summary_table <- results_lmm %>%
  left_join(repeatability, by = "Descriptor") %>%
  left_join(usage_rate,    by = "Descriptor") %>%
  mutate(
    flag_disc   = if_else(F_product >= median(F_product, na.rm = TRUE), "HIGH", "low"),
    flag_repeat = if_else(Repeatability_r >= 0.6, "OK", "weak"),
    flag_usage  = if_else(UsageRate >= 0.35, "OK", "low"),
    Decision = case_when(
      flag_disc == "HIGH" & flag_repeat == "OK" & flag_usage == "OK" ~ "GIU",
      flag_disc == "low"  & flag_repeat == "weak"                     ~ "LOAI",
      flag_disc == "HIGH" & flag_usage  == "low"                      ~ "XEM LAI (usage thap)",
      flag_disc == "low"  & flag_repeat == "OK"                       ~ "XEM LAI (F thap)",
      TRUE                                                             ~ "XEM LAI"
    )
  ) %>%
  arrange(desc(eta2))

cat("=== Bảng tổng hợp ===\n")
print(summary_table %>%
  select(Descriptor, F_product, sig, eta2, Repeatability_r, UsageRate, Decision),
  n = Inf)
cat("\n")

# ------------------------------------------------------------
# 5. TƯƠNG QUAN GIỮA DESCRIPTORS
# Đặc biệt chú ý cặp M.sua / H.sua
# ------------------------------------------------------------
desc_means <- df %>%
  group_by(Panelist, Product) %>%
  summarise(across(all_of(desc_cols), mean, na.rm = TRUE), .groups = "drop") %>%
  select(all_of(desc_cols))

cor_matrix <- cor(desc_means, use = "complete.obs") %>% round(3)

# Cặp có r > 0.80
high_cor_pairs <- which(abs(cor_matrix) > 0.80 & upper.tri(cor_matrix), arr.ind = TRUE)
cat("=== Cặp descriptors có r > 0.80 ===\n")
if (nrow(high_cor_pairs) > 0) {
  for (i in seq_len(nrow(high_cor_pairs))) {
    r <- cor_matrix[high_cor_pairs[i,1], high_cor_pairs[i,2]]
    cat(sprintf("  %-15s <-> %-15s  r = %.3f\n",
      rownames(cor_matrix)[high_cor_pairs[i,1]],
      colnames(cor_matrix)[high_cor_pairs[i,2]], r))
  }
} else {
  cat("  Không có cặp nào\n")
}

# In riêng cặp M.sua / H.sua
cat(sprintf("\n  M.sua <-> H.sua: r = %.3f\n\n", cor_matrix["M.sua", "H.sua"]))

# ------------------------------------------------------------
# 6. VISUALIZATION
# ------------------------------------------------------------

# 6a. Bubble plot
p1 <- summary_table %>%
  ggplot(aes(x = Repeatability_r, y = F_product,
             size = UsageRate, color = Decision, label = Descriptor)) +
  geom_point(alpha = 0.8) +
  ggrepel::geom_text_repel(
    size          = 3,
    max.overlaps  = Inf,       # không bỏ label nào
    box.padding   = 0.4,
    point.padding = 0.3,
    segment.color = "gray70",
    segment.size  = 0.3
  ) +
  geom_vline(xintercept = 0.6, linetype = "dashed", color = "gray50") +
  geom_hline(yintercept = median(summary_table$F_product, na.rm = TRUE),
             linetype = "dashed", color = "gray50") +
  scale_size_continuous(range = c(3, 10), labels = scales::percent) +
  scale_color_manual(values = c(
    "GIU"                  = "#2E7D32",
    "LOAI"                 = "#C62828",
    "XEM LAI"              = "#F57F17",
    "XEM LAI (F thap)"     = "#E65100",
    "XEM LAI (usage thap)" = "#6A1B9A"
  )) +
  labs(
    title    = "Discriminating Power vs Repeatability",
    subtitle = "Bubble size = Usage Rate | Đường kẻ = median cutoffs",
    x        = "Repeatability r (Rep1 vs Rep2)",
    y        = "F-ratio (Product effect)",
    size     = "Usage Rate",
    color    = "Quyết định"
  ) +
  theme_bw(base_size = 11)

# Thử dùng ggrepel nếu có, nếu không thì geom_text thường
tryCatch({
  library(ggrepel)
  p1 <- p1
}, error = function(e) {
  p1 <<- p1 + geom_text_repel(
    size          = 3,
    max.overlaps  = Inf,       # không bỏ label nào
    box.padding   = 0.4,
    point.padding = 0.3,
    segment.color = "gray70",
    segment.size  = 0.3
  )
})

print(p1)
ggsave("descriptor_bubble.png", p1, width = 10, height = 7, dpi = 150)

# 6b. Heatmap tương quan
# cor_long <- melt(cor_matrix)
cor_long <- as.data.frame(cor_matrix) %>%
  rownames_to_column("Var1") %>%
  pivot_longer(-Var1, names_to = "Var2", values_to = "value")

p2 <- ggplot(cor_long, aes(Var1, Var2, fill = value)) +
  geom_tile(color = "white") +
  geom_text(aes(label = sprintf("%.2f", value)), size = 2) +
  scale_fill_gradient2(low = "#2166AC", mid = "white", high = "#D6604D",
                       midpoint = 0, limits = c(-1, 1)) +
  labs(title = "Tương quan giữa descriptors", x = NULL, y = NULL, fill = "r") +
  theme_bw(base_size = 9) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 7),
        axis.text.y = element_text(size = 7))

print(p2)
ggsave("descriptor_correlation.png", p2, width = 10, height = 9, dpi = 150)

cat("=== DONE ===\n")
cat("Plots đã lưu: descriptor_bubble.png, descriptor_correlation.png\n")


# Đánh giá năng lực từng thành viên

res<-paneliperf(df1, formul = "~Product+Panelist+Repetition+
  Product:Panelist+Product:Repetition+Panelist:Repetition",
                formul.j = "~Product", col.j = 1, firstvar = 4, synthesis = TRUE)

resprob<-magicsort(res$prob.ind, method = "median")
coltable(resprob, level.lower = 0.05, level.upper = 1,
         main.title = "P-value of the F-test (by panelist)")
hist(resprob,main="Histogram of the P-values",xlab="P-values")

resagree<-magicsort(res$agree, sort.mat = res$r2.ind, method = "median")
X11()
coltable(resagree, level.lower = 0.00, level.upper = 0.85,
         main.title = "Agreement between panelists")
X11()
hist(resagree,main="Histogram of the agreement between panelist and panel",
     xlab="Correlation coefficient between the product effect for 
    panelist and panel")
#========================================================
  
# ---- Tóm tắt năng lực panelist ----

# 1. Discrimination: đếm số descriptor có p < 0.05 cho từng panelist
disc_summary <- as.data.frame(res$prob.ind) %>%
  rownames_to_column("Panelist") %>%
  pivot_longer(-Panelist, names_to = "Descriptor", values_to = "pval") %>%
  group_by(Panelist) %>%
  summarise(
    n_sig      = sum(pval < 0.05, na.rm = TRUE),
    n_total    = sum(!is.na(pval)),
    pct_sig    = round(n_sig / n_total * 100, 1),
    median_p   = round(median(pval, na.rm = TRUE), 3)
  ) %>%
  arrange(pct_sig)

cat("=== Discrimination (% descriptors có p < 0.05) ===\n")
print(disc_summary, n = Inf)

# 2. Agreement: ai đang ngược chiều panel (r âm hoặc thấp)
agree_summary <- as.data.frame(res$agree) %>%
  rownames_to_column("Panelist") %>%
  pivot_longer(-Panelist, names_to = "Descriptor", values_to = "r") %>%
  group_by(Panelist) %>%
  summarise(
    median_r   = round(median(r, na.rm = TRUE), 3),
    n_negative = sum(r < 0,    na.rm = TRUE),
    n_low      = sum(r < 0.3,  na.rm = TRUE),
    n_total    = sum(!is.na(r))
  ) %>%
  arrange(median_r)   # người có r thấp nhất lên đầu

cat("\n=== Agreement với panel (r thấp = ngược chiều) ===\n")
print(agree_summary, n = Inf)

# 3. Flag ai đáng lo — disc thấp VÀ agreement thấp
cat("\n=== Panelists cần chú ý ===\n")
flags <- disc_summary %>%
  left_join(agree_summary, by = "Panelist") %>%
  filter(pct_sig < 30 | median_r < 0.3 | n_negative > 2) %>%
  arrange(median_r)

print(flags %>% select(Panelist, pct_sig, median_r, n_negative), n = Inf)
