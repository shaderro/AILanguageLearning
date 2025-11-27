import { useState } from 'react';
import { BaseInput } from './BaseInput';

export function BaseInputDemo() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div className="space-y-6 max-w-xl">
      <BaseInput
        label="邮箱"
        placeholder="请输入邮箱地址"
        helperText="我们会通过邮箱联系你"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />

      <BaseInput
        label="密码"
        type="password"
        placeholder="请输入至少 6 位密码"
        helperText="密码必须包含字母与数字"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        size="lg"
      />

      <BaseInput
        label="邀请码"
        placeholder="可选"
        helperText="如没有可留空"
        prefix="#"
        variant="filled"
      />

      <BaseInput
        label="验证码"
        placeholder="请输入验证码"
        error="验证码不正确"
        suffix={<span className="text-sm text-primary-600 cursor-pointer">重新发送</span>}
      />
    </div>
  );
}


