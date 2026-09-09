# 第二次正式尝试停止记录

实际进程 proc_51f5901fa58d 退出码1。FORMAL_ATTEMPT 回读确认第二次预算已消费，正式预算2/2，无重试许可。

FORMAL_FAILURE 保存实际 traceback：external29_driver.py:662 → policy_builder.py:66，PREBOUND_ELIGIBLE_MANIFEST_CHANGED。这是 policy 构建失败，不是产品断言失败，也不是一次已接受 baseline 后的失败。具体差异及写者尚未确定，不能仅凭异常名称归因。

29 REQUIRED / 0 PASS / 0 产品门禁 FAIL / 29 NOT_RUN；baseline、seal、START 未生成。8000身份及29 skipped仍仅为预期，完整后端未执行。

此前 prepare/identity/endpoints/revalidate/disposition 的成功记录保留；这些检查没有阻止此次实际 policy 构建拒绝，不能据此前 READY 宣称完整工程通过。

工程未通过，EP19未关闭。已启动独立失败审查及脱敏交付准备 deleg_ef473671；不得刷新 map、policy、baseline，不改执行器或产品后重跑。共享正文不写、不恢复。
