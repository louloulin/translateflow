import React, { useState, useEffect } from 'react';
import { Clock, Plus, Trash2, Play, Square, Edit3, FolderOpen, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { DataService } from '../services/DataService';
import { useI18n } from '../contexts/I18nContext';
import { useGlobal } from '../contexts/GlobalContext';

interface ScheduledTask {
    task_id: string;
    name: string;
    schedule: string;
    input_path: string;
    profile: string;
    task_type: string;
    enabled: boolean;
    next_run?: string;
    last_run?: string;
}

export const Scheduler: React.FC = () => {
    const { t } = useI18n();
    const { profiles, activeTheme } = useGlobal();
    const [tasks, setTasks] = useState<ScheduledTask[]>([]);
    const [status, setStatus] = useState<{ running: boolean; task_count: number }>({ running: false, task_count: 0 });
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editTask, setEditTask] = useState<ScheduledTask | null>(null);
    const [logs, setLogs] = useState<any[]>([]);
    const [showLogs, setShowLogs] = useState(false);

    // Task Form State
    const [taskForm, setTaskForm] = useState({
        task_id: '',
        name: '',
        schedule: '0 2 * * *',
        input_path: '',
        profile: '',
        task_type: 'translation',
        enabled: true
    });

    const fetchData = async () => {
        try {
            const [statusData, tasksData] = await Promise.all([
                DataService.getSchedulerStatus(),
                DataService.getSchedulerTasks()
            ]);
            setStatus(statusData);
            setTasks(tasksData);
        } catch (error) {
            console.error("Failed to fetch scheduler data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const openAddModal = () => {
        setEditTask(null);
        setTaskForm({
            task_id: '',
            name: '',
            schedule: '0 2 * * *',
            input_path: '',
            profile: profiles[0] || '',
            task_type: 'translation',
            enabled: true
        });
        setShowModal(true);
    };

    const openEditModal = (task: ScheduledTask) => {
        setEditTask(task);
        setTaskForm({
            task_id: task.task_id,
            name: task.name,
            schedule: task.schedule,
            input_path: task.input_path,
            profile: task.profile,
            task_type: task.task_type,
            enabled: task.enabled
        });
        setShowModal(true);
    };

    const handleSubmit = async () => {
        try {
            if (editTask) {
                await DataService.updateSchedulerTask(taskForm.task_id, {
                    enabled: taskForm.enabled,
                    schedule: taskForm.schedule,
                    input_path: taskForm.input_path,
                    profile: taskForm.profile
                });
            } else {
                await DataService.addSchedulerTask(taskForm);
            }
            setShowModal(false);
            fetchData();
        } catch (error) {
            console.error("Failed to save task", error);
            alert(String(error));
        }
    };

    const handleDelete = async (taskId: string) => {
        if (!confirm(t('confirm_delete') || 'Are you sure you want to delete this task?')) {
            return;
        }
        try {
            await DataService.deleteSchedulerTask(taskId);
            fetchData();
        } catch (error) {
            console.error("Failed to delete task", error);
            alert(String(error));
        }
    };

    const handleToggle = async (task: ScheduledTask) => {
        try {
            await DataService.updateSchedulerTask(task.task_id, { enabled: !task.enabled });
            fetchData();
        } catch (error) {
            console.error("Failed to toggle task", error);
        }
    };

    const handleToggleScheduler = async () => {
        try {
            if (status.running) {
                await DataService.stopScheduler();
            } else {
                await DataService.startScheduler();
            }
            fetchData();
        } catch (error) {
            console.error("Failed to toggle scheduler", error);
        }
    };

    const handleViewLogs = async () => {
        try {
            const logsData = await DataService.getSchedulerLogs();
            setLogs(logsData);
            setShowLogs(true);
        } catch (error) {
            console.error("Failed to fetch logs", error);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: activeTheme.primary }}></div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <Clock className="w-6 h-6" style={{ color: activeTheme.primary }} />
                    <h1 className="text-2xl font-bold">{t('scheduler_title') || 'Scheduled Tasks'}</h1>
                </div>
                <div className="flex items-center space-x-2">
                    <button
                        onClick={handleToggleScheduler}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                            status.running
                                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                        }`}
                    >
                        {status.running ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                        <span>{status.running ? (t('stop') || 'Stop') : (t('start') || 'Start')}</span>
                    </button>
                    <button
                        onClick={handleViewLogs}
                        className="px-4 py-2 rounded-lg bg-slate-700/50 text-slate-300 hover:bg-slate-700 transition-colors"
                    >
                        {t('view_logs') || 'View Logs'}
                    </button>
                    <button
                        onClick={openAddModal}
                        className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors"
                        style={{ backgroundColor: activeTheme.primary + '20', color: activeTheme.primary }}
                    >
                        <Plus className="w-4 h-4" />
                        <span>{t('add_task') || 'Add Task'}</span>
                    </button>
                </div>
            </div>

            {/* Status Banner */}
            <div className={`p-4 rounded-lg flex items-center justify-between ${
                status.running ? 'bg-green-500/10 border border-green-500/20' : 'bg-slate-700/30 border border-slate-700'
            }`}>
                <div className="flex items-center space-x-3">
                    {status.running ? (
                        <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                        <XCircle className="w-5 h-5 text-slate-400" />
                    )}
                    <span className={status.running ? 'text-green-400' : 'text-slate-400'}>
                        {status.running ? (t('scheduler_running') || 'Scheduler is running') : (t('scheduler_stopped') || 'Scheduler is stopped')}
                    </span>
                </div>
                <span className="text-slate-400">
                    {status.task_count} {t('tasks') || 'tasks'}
                </span>
            </div>

            {/* Task List */}
            {tasks.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                    <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>{t('no_scheduled_tasks') || 'No scheduled tasks configured'}</p>
                    <button
                        onClick={openAddModal}
                        className="mt-4 px-4 py-2 rounded-lg transition-colors"
                        style={{ backgroundColor: activeTheme.primary + '20', color: activeTheme.primary }}
                    >
                        {t('create_first_task') || 'Create your first task'}
                    </button>
                </div>
            ) : (
                <div className="grid gap-4">
                    {tasks.map((task) => (
                        <div
                            key={task.task_id}
                            className="p-4 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-slate-600 transition-colors"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-4">
                                    <button
                                        onClick={() => handleToggle(task)}
                                        className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                                            task.enabled
                                                ? 'bg-green-500/20 text-green-400'
                                                : 'bg-slate-700 text-slate-400'
                                        }`}
                                    >
                                        {task.enabled ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                                    </button>
                                    <div>
                                        <h3 className="font-semibold text-slate-200">{task.name}</h3>
                                        <p className="text-sm text-slate-400">
                                            <span className="font-mono">{task.schedule}</span>
                                            {' • '}
                                            {task.profile}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <span className={`px-2 py-1 rounded text-xs ${
                                        task.task_type === 'translation'
                                            ? 'bg-blue-500/20 text-blue-400'
                                            : task.task_type === 'polishing'
                                            ? 'bg-purple-500/20 text-purple-400'
                                            : 'bg-orange-500/20 text-orange-400'
                                    }`}>
                                        {task.task_type}
                                    </span>
                                    <button
                                        onClick={() => openEditModal(task)}
                                        className="p-2 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
                                    >
                                        <Edit3 className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(task.task_id)}
                                        className="p-2 rounded-lg hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                            <div className="mt-3 flex items-center space-x-4 text-sm text-slate-500">
                                <div className="flex items-center space-x-1">
                                    <FolderOpen className="w-4 h-4" />
                                    <span className="truncate max-w-md">{task.input_path}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Add/Edit Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-slate-800 rounded-lg p-6 w-full max-w-md border border-slate-700">
                        <h2 className="text-xl font-bold mb-4">
                            {editTask ? (t('edit_task') || 'Edit Task') : (t('add_task') || 'Add Task')}
                        </h2>
                        <div className="space-y-4">
                            {!editTask && (
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-1">
                                        {t('task_id') || 'Task ID'}
                                    </label>
                                    <input
                                        type="text"
                                        value={taskForm.task_id}
                                        onChange={(e) => setTaskForm({ ...taskForm, task_id: e.target.value })}
                                        className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-200"
                                        placeholder="daily-translation"
                                    />
                                </div>
                            )}
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">
                                    {t('task_name') || 'Task Name'}
                                </label>
                                <input
                                    type="text"
                                    value={taskForm.name}
                                    onChange={(e) => setTaskForm({ ...taskForm, name: e.target.value })}
                                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-200"
                                    placeholder="Daily Translation"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">
                                    {t('cron_expression') || 'Cron Expression'}
                                </label>
                                <input
                                    type="text"
                                    value={taskForm.schedule}
                                    onChange={(e) => setTaskForm({ ...taskForm, schedule: e.target.value })}
                                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-200 font-mono"
                                    placeholder="0 2 * * *"
                                />
                                <p className="text-xs text-slate-500 mt-1">
                                    {t('cron_hint') || 'Format: minute hour day month weekday'}
                                </p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">
                                    {t('input_path') || 'Input Path'}
                                </label>
                                <input
                                    type="text"
                                    value={taskForm.input_path}
                                    onChange={(e) => setTaskForm({ ...taskForm, input_path: e.target.value })}
                                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-200"
                                    placeholder="/path/to/input"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">
                                    {t('profile') || 'Profile'}
                                </label>
                                <select
                                    value={taskForm.profile}
                                    onChange={(e) => setTaskForm({ ...taskForm, profile: e.target.value })}
                                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-200"
                                >
                                    {profiles.map((profile) => (
                                        <option key={profile} value={profile}>{profile}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">
                                    {t('task_type') || 'Task Type'}
                                </label>
                                <select
                                    value={taskForm.task_type}
                                    onChange={(e) => setTaskForm({ ...taskForm, task_type: e.target.value })}
                                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-200"
                                >
                                    <option value="translation">{t('task_type_translation') || 'Translation'}</option>
                                    <option value="polishing">{t('task_type_polishing') || 'Polishing'}</option>
                                    <option value="all_in_one">{t('task_type_all_in_one') || 'All in One'}</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex justify-end space-x-3 mt-6">
                            <button
                                onClick={() => setShowModal(false)}
                                className="px-4 py-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
                            >
                                {t('cancel') || 'Cancel'}
                            </button>
                            <button
                                onClick={handleSubmit}
                                className="px-4 py-2 rounded-lg transition-colors"
                                style={{ backgroundColor: activeTheme.primary, color: 'white' }}
                            >
                                {t('save') || 'Save'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Logs Modal */}
            {showLogs && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-slate-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] border border-slate-700 flex flex-col">
                        <h2 className="text-xl font-bold mb-4">{t('scheduler_logs') || 'Scheduler Logs'}</h2>
                        <div className="flex-1 overflow-auto bg-slate-900 rounded p-4 font-mono text-sm">
                            {logs.length === 0 ? (
                                <p className="text-slate-400">{t('no_logs') || 'No logs available'}</p>
                            ) : (
                                logs.map((log, index) => (
                                    <div key={index} className="text-slate-300 mb-1">
                                        <span className="text-slate-500">[{new Date(log.timestamp * 1000).toLocaleString()}]</span>{' '}
                                        {log.message}
                                    </div>
                                ))
                            )}
                        </div>
                        <div className="flex justify-end mt-4">
                            <button
                                onClick={() => setShowLogs(false)}
                                className="px-4 py-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
                            >
                                {t('close') || 'Close'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
