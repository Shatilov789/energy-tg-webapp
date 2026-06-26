import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import {
  IconBuildingFactory,
  IconLineDashed,
  IconBolt,
  IconTool,
  IconClipboardCheck,
  IconChevronLeft,
  IconChevronDown,
  IconCheck,
  IconCircleCheck,
  IconFileText,
} from '@tabler/icons-react';

const SCENARIO_ICONS = {
  'Подстанция': { icon: IconBuildingFactory, cls: 'ci-a', chipCls: 'step-chip-a' },
  'КЛ линия': { icon: IconLineDashed, cls: 'ci-b', chipCls: 'step-chip-b' },
  'Трансформатор': { icon: IconBolt, cls: 'ci-r', chipCls: 'step-chip-r' },
  'Ремонт': { icon: IconTool, cls: 'ci-g', chipCls: 'step-chip-g' },
  'Проверка оборудования': { icon: IconClipboardCheck, cls: 'ci-p', chipCls: 'step-chip-p' },
};

export default function ObjectsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const scenarioId = searchParams.get('scenario');

  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [newName, setNewName] = useState('');
  const [newComment, setNewComment] = useState('');
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const showLoadingText = useDelayedLoadingText(loading);
  const dropdownRef = useRef(null);

  useEffect(() => { loadData(); }, []);

  useEffect(() => {
    if (!dropdownOpen) return;
    function onClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, [dropdownOpen]);

  async function loadData() {
    try {
      const data = await api.getScenarios();
      setScenarios(data);
      if (scenarioId) {
        const found = data.find(s => s.id === Number(scenarioId));
        if (found) setSelectedScenario(found);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!newName.trim() || !selectedScenario) return;
    setCreating(true);
    try {
      const obj = await api.createObject({
        name: newName.trim(),
        comment: newComment.trim() || null,
        scenario_id: selectedScenario.id,
      });
      navigate(`/objects/${obj.id}/steps/1`);
    } catch (err) {
      alert(err.message);
    } finally {
      setCreating(false);
    }
  }

  function getIcon(name) {
    return SCENARIO_ICONS[name] || { icon: IconFileText, cls: 'ci-a', chipCls: 'step-chip-default' };
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Загрузка...' : ''}</div>;

  const canSubmit = newName.trim().length > 0 && selectedScenario !== null;

  return (
    <div className="page">
      <div className="tbar">
        <button className="btn-bk" onClick={() => navigate('/')}>
          <IconChevronLeft size={20} />
        </button>
        <div style={{ fontSize: 18, fontWeight: 700 }}>Новый объект</div>
      </div>

      <div className="sc" style={{ paddingBottom: 32 }}>
        <div className="fgrp" style={{ marginTop: 4 }}>
          <label className="flbl">Наименование объекта</label>
          <input
            className="finp"
            type="text"
            placeholder="ПС 110/10 кВ «Название»"
            value={newName}
            onChange={e => setNewName(e.target.value)}
          />
        </div>

        <div className="fgrp">
          <label className="flbl">Адрес / Комментарий</label>
          <textarea
            className="finp"
            rows={3}
            placeholder="ул. Промышленная, 14..."
            style={{ resize: 'none', lineHeight: 1.5 }}
            value={newComment}
            onChange={e => setNewComment(e.target.value)}
          />
        </div>

        <div className="fgrp">
          <label className="flbl">Сценарий инспекции</label>
          <div className="scen-select" ref={dropdownRef}>
            <button
              type="button"
              className="scen-select-trigger"
              onClick={() => setDropdownOpen(o => !o)}
            >
              {selectedScenario ? (() => {
                const { icon: IconComp, cls } = getIcon(selectedScenario.name);
                return (
                  <span className="scen-select-current">
                    <span className={`ci ${cls}`} style={{ width: 28, height: 28 }}>
                      <IconComp size={16} />
                    </span>
                    {selectedScenario.name}
                  </span>
                );
              })() : (
                <span className="scen-select-placeholder">Выберите сценарий...</span>
              )}
              <IconChevronDown size={18} className={`scen-select-arrow ${dropdownOpen ? 'open' : ''}`} />
            </button>

            {dropdownOpen && (
              <div className="scen-select-panel">
                {scenarios.map(s => {
                  const { icon: IconComp, cls } = getIcon(s.name);
                  const isSel = selectedScenario?.id === s.id;
                  return (
                    <div
                      key={s.id}
                      className={`scen-select-option ${isSel ? 'sel' : ''}`}
                      onClick={() => { setSelectedScenario(s); setDropdownOpen(false); }}
                    >
                      <span className={`ci ${cls}`} style={{ width: 28, height: 28 }}>
                        <IconComp size={16} />
                      </span>
                      <span style={{ flex: 1 }}>{s.name}</span>
                      {isSel && <IconCheck size={16} color="var(--acc)" />}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {selectedScenario && (() => {
            const { icon: IconComp, cls, chipCls } = getIcon(selectedScenario.name);
            const steps = selectedScenario.steps || [];
            return (
              <div className="scen-card sel" style={{ marginTop: 8 }}>
                <div className="scen-top">
                  <div className={`ci ${cls}`} style={{ width: 36, height: 36 }}>
                    <IconComp size={20} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div className="scen-title">{selectedScenario.name}</div>
                    <div className="scen-sub">
                      {steps.length} вопросов · {selectedScenario.description}
                    </div>
                  </div>
                </div>
                {steps.length > 0 && (
                  <div className="scen-steps">
                    {steps.slice(0, 5).map((st, i) => (
                      <span className={`step-chip ${chipCls}`} key={i}>
                        {st.question_text?.length > 18
                          ? st.question_text.substring(0, 18) + '…'
                          : st.question_text}
                      </span>
                    ))}
                    {steps.length > 5 && (
                      <span className="step-chip step-chip-default">+{steps.length - 5}</span>
                    )}
                  </div>
                )}
              </div>
            );
          })()}
        </div>

        <button
          className="btn-p"
          onClick={handleCreate}
          disabled={creating || !canSubmit}
          style={{
            background: canSubmit ? 'var(--acc)' : 'var(--s3)',
            color: canSubmit ? '#17171A' : 'var(--mu)',
            cursor: canSubmit ? 'pointer' : 'not-allowed',
            marginBottom: 32,
          }}
        >
          <IconCircleCheck size={18} />
          {creating ? 'Создание...' : 'Создать объект и начать'}
        </button>
      </div>
    </div>
  );
}
