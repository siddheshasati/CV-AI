"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Save, CheckCircle } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type UserSettings } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getSettings()
      .then(setSettings)
      .finally(() => setLoading(false));
  }, []);

  const update = (patch: Partial<UserSettings>) => {
    if (!settings) return;
    setSettings({ ...settings, ...patch });
    setSaved(false);
  };

  const handleSave = async () => {
    if (!settings) return;
    await api.updateSettings(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="gradient-bg min-h-dvh">
      <Header />

      <main className="mx-auto max-w-2xl p-4 md:p-8">
        <Link
          href="/"
          className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground transition hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Voice
        </Link>

        <h1 className="mb-6 text-2xl font-bold">Settings</h1>

        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : settings ? (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Preferences</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium">Language</label>
                  <select
                    value={settings.language}
                    onChange={(e) => update({ language: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm focus:border-violet-500/50 focus:outline-none"
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="ja">Japanese</option>
                  </select>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Auto Web Search</p>
                    <p className="text-xs text-muted-foreground">
                      Automatically search when the AI needs current info
                    </p>
                  </div>
                  <Switch
                    checked={settings.auto_search}
                    onCheckedChange={(v) => update({ auto_search: v })}
                  />
                </div>
              </CardContent>
            </Card>

            <Button onClick={handleSave} className="w-full gap-2">
              {saved ? (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Saved!
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Settings
                </>
              )}
            </Button>
          </div>
        ) : null}
      </main>
    </div>
  );
}
